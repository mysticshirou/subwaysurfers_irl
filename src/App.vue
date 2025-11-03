<template>
  <div class="app">
    <div class="webcam-container">
      <Camera :syncStatus="sync"/>
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
        socket: null,
        sync: false
      }
    },
    methods: {
      simulateKeyPress(key, code, keyCode) {
        const canvas = this.$refs.subwaySurfers.$refs.unityContainer.querySelector('canvas');
        if (!canvas) return "Socketio Client: Canvas not found";

        const down = new KeyboardEvent('keydown', { key, code, keyCode, bubbles: true });
        const up = new KeyboardEvent('keyup', { key, code, keyCode, bubbles: true });
        canvas.dispatchEvent(down);
        canvas.dispatchEvent(up);
      }
    },
    mounted() {
      // Initialise SocketIO Client
      this.socket = io('http://127.0.0.1:5000')

      // Listen for Flask events
      this.socket.on('triggerKeyboard', (data) => {
        console.log('Event received:', data)
        this.simulateKeyPress(data.key, data.key, data.code)
      })

      this.socket.on('syncStatus', (syncState) => {
        this.sync = syncState
      })

      this.socket.on('connectionTest', (msg) => {
        alert('JS function triggered by Flask: ' + msg.message);
      })
    },
    beforeUnmount() {
      // Clean up the listener when the component is destroyed
      this.socket.off('triggerKeyboard')
      this.socket.off("connectionTest")
    }
  }
</script>

<style scoped>
  .app {
    display: flex;
    padding-block: 5vh;
    padding-inline: 5vh;
    column-gap: 5vh; /* .app (100%) = .webcam-container (x) + column-gap (y) + .game-container (z)*/

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
    width: 55%; /* .app (100%) = .webcam-container (x) + column-gap (y) + .game-container (z)*/
    height: 100%;

    /* border: 3px blue solid; */
    border-radius: 8px;
    box-shadow: 0 0 16px #aaaaaa;
    overflow: hidden;
  }

  .game-container {
    width: 45%; /* .app (100%) = .webcam-container (x) + column-gap (y) + .game-container (z)*/
    height: 100%;

    /* border: 3px red solid; */
    border-radius: 8px;
    box-shadow: 0 0 16px #aaaaaa;
    overflow: hidden;
  }
</style>
