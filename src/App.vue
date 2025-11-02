<template>
  <div class="app">
    <div class="webcam-container">
      <Camera/>
    </div>
    <div class="game-container">
      <SubwaySurfers ref="subwaySurfers"/>
    </div>
  </div>
</template>

<script>
import { io } from 'socket.io-client'
import Camera from './components/Camera.vue';
import SubwaySurfers from './components/SubwaySurfers.vue';

  export default {
    components: { SubwaySurfers, Camera },
    data() {
      return {
        socket: null
      }
    },
    methods: {
      simulateKeyPress(key, code, keyCode) {
        const canvas = this.$refs.subwaySurfers.$refs.unityContainer.querySelector('canvas');
        if (!canvas) return;

        const down = new KeyboardEvent('keydown', { key, code, keyCode, bubbles: true });
        const up = new KeyboardEvent('keyup', { key, code, keyCode, bubbles: true });
        canvas.dispatchEvent(down);
        canvas.dispatchEvent(up);
      }
    },
    mounted() {
      // Initialise SocketIO Client
      this.socket = io('http://127.0.0.1:5000')

      this.socket.on('connect', () => {
        console.log('Connected to server');
      });

      this.socket.on('connect_error', (err) => {
        console.error('Connection error:', err);
      });

      this.socket.on('connection_test', (msg) => {
        alert('JS function triggered by Flask: ' + msg.msg);
      })

      // Listen for Flask events
      // this.socket.on('triggerKeyboard', (data) => {
      //   console.log('Event received:', data)
      //   this.simulateKeyPress(data.key, data.key, data.code)
      // })

      // // Listen for Flask events
      // this.socket.on('triggerKeyboard', (data) => {
      //   console.log('Event received:', data)
      //   this.simulateKeyPress(data.key, data.key, data.code)
      // })
    },
    beforeUnmount() {
      // Clean up the listener when the component is destroyed
      this.off('triggerKeyboard')
    }
  }
</script>

<style scoped>
  .app {
    display: flex;
    padding-block: 5vh;
    padding-inline: 5vh;
    column-gap: 5vh; /* .app (100%) = .webcam-container (35%) + column-gap (5%) + .game-container (60%)*/

    width: 100vw;
    height: 100vh;
    overflow: hidden;

    --background-colour: hsl(216, 28%, 7%);
    --grid-lines-colour: hsl(0, 0%, 15%);
    background-image:
      linear-gradient(var(--grid-lines-colour) 1px, transparent 1px),
      linear-gradient(to right, var(--grid-lines-colour) 1px, var(--background-colour) 1px);
    background-size: 40px 40px;
  }

  .webcam-container {
    width: 35%; /* .app (100%) = .webcam-container (35%) + column-gap (5%) + .game-container (60%)*/
    height: 100%;

    /* border: 3px blue solid; */
    border-radius: 8px;
    box-shadow: 0 0 16px #aaaaaa;
    overflow: hidden;
  }

  .game-container {
    width: 60%; /* .app (100%) = .webcam-container (35%) + column-gap (5%) + .game-container (60%)*/
    height: 100%;

    /* border: 3px red solid; */
    border-radius: 8px;
    box-shadow: 0 0 16px #aaaaaa;
    overflow: hidden;
  }
</style>
