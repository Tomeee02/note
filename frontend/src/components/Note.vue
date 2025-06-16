<template>
  <div class="note" @dragover.prevent @drop="handleDrop">
    <textarea v-model="content"></textarea>
    <button @click="deleteNote">Törlés</button>
  </div>
</template>

<script>
export default {
  props: ['id', 'initialContent'],
  data() {
    return { content: this.initialContent || '', files: [] };
  },
  methods: {
    handleDrop(event) {
      event.preventDefault();
      const droppedFile = event.dataTransfer.files[0];
      this.files.push(droppedFile);
      console.log('Fájl feltöltve:', droppedFile.name);
    },
    deleteNote() { this.$emit('delete', this.id); }
  }
};
</script>

<style scoped>
.note { position: absolute; background: yellow; padding: 10px; cursor: move; }
</style>
