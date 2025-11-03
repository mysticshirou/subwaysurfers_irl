!<template>
  <div class="webcam-wrapper">
    <p class="sync-text" :style="syncText">Player not found. Recalibrating...</p>
    <img :src="videoUrl" alt="" id="webcam"/>
    <p>Video Stream Loading...</p>
  </div>
</template>

<script>
  export default {
    props: ["syncStatus"],
    data() {
      return {
        // videoUrl: "http://127.0.0.1:5000/webcam-feed",
        videoUrl: "https://images.unsplash.com/photo-1761872936204-07e2bbe1990b?ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&q=80&w=1170",
      }
    },
    computed: {
      syncText() {
        return this.syncStatus ? "display: None" : ""
      }
    }
  }
</script>

<style scoped>
  .webcam-wrapper {
    width: 100%;
    height: 100%;

    display: grid;
    grid-template-columns: 1fr;
    grid-template-rows: 1fr;

    place-items: center;
    align-content: center;
  }

  .webcam-wrapper > * {
    grid-area: 1 / 1;
  }

  .sync-text {
    z-index: 2;
    width: 100%;
    height: 100%;

    background: rgba(0, 0, 0, 0.8);

    display: flex;
    justify-content: center;
    align-items: center;
  }

  img {
    z-index: 1;
    width: 100%;
    height: 100%;

    object-fit: cover;
  }

  p {
    color: white;
    font-family: Arial, Helvetica, sans-serif;
    font-size: 5.5rem;
    text-align: center;
    font-style: bold;
    font-weight: bolder;
    text-shadow: 0 0 5px #aaaaaa;
  }
</style>
