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
        videoUrl: "http://127.0.0.1:5000/webcam-feed",
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
