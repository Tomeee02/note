<template>
  <div class="board" @dblclick="addNote">
    <Note
      v-for="note in notes"
      :key="note.id"
      :id="note.id"
      :initialContent="note.content"
      @delete="deleteNote"
    />
  </div>
</template>

<script>
import Note from './Note.vue';

export default {
  components: { Note },
  data() {
    return { notes: [] };
  },
  methods: {
    addNote(event) {
      const newNote = { id: Date.now(), content: "Új jegyzet" };
      this.notes.push(newNote);
    },
    deleteNote(id) {
      this.notes = this.notes.filter(note => note.id !== id);
    }
  }
};
</script>

<style scoped>
.board {
  width: 100%;
  height: 100vh;
  background-color: #f0f0f0;
  position: relative;
}
</style>
