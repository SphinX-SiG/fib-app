var progressBar = {
  props: ['message', 'result'],
  template: `
    <div v-if="result.length > 0">
      <ul>
      <li v-for="item in result" :key="item.pos"> {{ item.pos }}: {{ item.val }} </li>
      </ul>
    </div>
    <div v-else>
      <h3> {{ message }} </h3>
    </div>
    `
};

var userControls = {
  props: ["from", "to"],
  template: `
    <div id="input-data">
      <label>From: <input type="number" v-model.number.trim="mutableFrom" /></label>
      <br>
      <label>To: <input type="number" v-model.number.trim="mutableTo" /></label>
      <br>
      <input type="radio" id="by_pos" value="by_pos" v-model="sliceType">
      <label for="by_pos">By position</label>
      <input type="radio" id="by_val" value="by_val" v-model="sliceType">
      <label for="by_val">By value</label>
      <br>
      <span>Выбрано: {{ sliceType }}</span>
      <br>
      <button class="btn btn-alt" name="get_sequence" @click="$parent.get_sequence(sliceType)">
        Get Sequence from {{ from }} to {{ to }}
      </button>
    </div>
  `,
  data: function() {
      return {
        mutableFrom: this.from,
        mutableTo: this.to,
        sliceType: 'by_pos'
    }
  },
  watch: {
    mutableFrom: function(newVal){
      if (newVal>=0) {
        this.$emit('update:from', newVal)
      } else {
        this.$emit('update:from', 0);
        this.mutableFrom = 0;
      }
    },
    mutableTo: function(newVal){
      if (newVal>=0) {
        this.$emit('update:to', newVal);
      } else {
        this.$emit('update:to', 0);
        this.mutableTo = 0;
      }
    }
  }
};


var counterApp = new Vue({
  components: {
    'user-controls': userControls,
    'progress-bar': progressBar
  },
  data: {
    counterBorders: {
      from: 0,
      to: 15
    },
    message: "The Fibonachi sequence will be displayed here",
    result: []
  },
  created: function () {
    this.ws = this.create_ws();
  },
  methods: {
    create_ws(){
      var vm = this;
      var ws = new WebSocket('ws://localhost:5000/fibo');
      ws.onerror = function(error) {console.log('Возникла ошибка: ' + error.message);};
      ws.onopen = function() {console.log('Соединение установлено.')}
      ws.onclose = function(event) {
        if (event.wasClean) {
          console.log('Cоединение закрыто. Код: ' + event.code + ' Причина: ' + event.reason);
        } else {
          console.log('Обрыв связи. Код: ' + event.code + ' Причина: ' + event.reason);
        }
      };
      ws.onmessage = function(msg) {
        var resp = JSON.parse(msg.data)
        if (resp.type == 'error') {
          vm.message = resp.message; 
          console.log(resp);
        } else if (resp.type == 'item') {
          vm.result.push(resp);
        }
      };
      return ws;
    },
    get_sequence(_sliceType) {

      var req = {"action": "count", "type": _sliceType, "from": this.counterBorders.from, "to": this.counterBorders.to};
      this.result = [];
      this.ws.send(JSON.stringify(req));
    }
  }
}).$mount("#app");