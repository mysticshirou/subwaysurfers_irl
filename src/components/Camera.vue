!<template>
  <div class="webcam-wrapper">
    <img :src="videoUrl" alt="" id="webcam"/>
    <p>Video Stream Loading...</p>
  </div>
</template>

<script>
  export default {
    data() {
      return {
        videoUrl: "http://127.0.0.1:5000/webcam-feed"
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
