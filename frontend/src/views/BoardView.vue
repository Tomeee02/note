<template>
  <nav class="topbar">
    <div class="topbar-left">
      <template v-if="board && board.id">
        <template v-for="(b, index) in boardAncestors" :key="b.id">
          <span
            class="breadcrumb-link"
            @click="goToBoard(b.id)"
            :style="{ cursor: b.id !== board.id ? 'pointer' : 'default' }"
          >
            {{ b.emoji }} {{ b.title }}
          </span>
          <span v-if="index < boardAncestors.length - 1"> › </span>
        </template>
      </template>
    </div>
    <div class="topbar-right">
      <button class="settings-btn" @click="openSettings">⚙️</button>
    </div>
  </nav>
  <div style="display: flex">
    <div class="toolbar">
      <!-- Ha nincs semmi kijelölve -->
      <template v-if="selectedNotes.length === 0 && selectedBoards.length === 0">
        <div class="template-icon" @click="createNote" title="Új jegyzet">📝</div>
        <div class="template-icon" @click="createBoard" title="Új board">📁</div>
        <div class="template-icon" @click="createDocument" title="Új dokumentum">📄</div>
      </template>
      <!-- Ha note van kijelölve -->
      <template v-else-if="selectedNotes.length > 0">
        <input
          type="color"
          :value="selectedNotes[0].background_color"
          :class="{ mixed: hasMixedColors }"
          @input="
            (e) => {
              selectedNotes.forEach((note) => (note.background_color = e.target.value))
            }
          "
          @change="
            (e) => {
              selectedNotes.forEach((note) => updateNoteStyle(note))
            }
          "
          title="Háttérszín"
        />
        <input
          type="color"
          :value="selectedNotes[0].text_color"
          @input="
            (e) => {
              selectedNotes.forEach((note) => (note.text_color = e.target.value))
            }
          "
          @change="
            (e) => {
              selectedNotes.forEach((note) => updateNoteStyle(note))
            }
          "
          title="Szövegszín"
        />
      </template>

      <!-- Ha board van kijelölve -->
      <template v-else-if="selectedBoards.length > 0">
        <div class="icon-picker">
          <div
            v-for="icon in availableIcons"
            :key="icon"
            :class="['emoji-option', { selected: icon === selectedBoards[0].emoji }]"
            @click="updateBoardIcon(selectedBoards[0], icon)"
            :title="icon"
          >
            {{ icon }}
          </div>
        </div>
      </template>
    </div>
    <!-- Main -->
    <div style="flex: 1; padding-left: 16px">
      <section>
        <div
          v-for="note in notes"
          :key="note.id"
          class="sticky-note"
          :class="{ selected: selectedNotes.some((n) => n.id === note.id) }"
          :style="{
            left: note.position_x + 'px',
            top: note.position_y + 'px',
            background: note.background_color,
            color: note.text_color,
            width: note.width + 'px',
            height: note.height + 'px',
            borderColor: note.background_color,
          }"
          @mousedown.stop="startDrag(note, $event)"
          @click.stop="(e) => toggleNoteSelection(note, e)"
        >
          <div v-if="!note.editing" @dblclick="note.editing = true">
            {{ note.content }}
          </div>
          <!-- Szerkesztés textarea-ban -->
          <textarea
            v-else
            v-model="note.content"
            @blur="finishEdit(note)"
            @keyup.enter.exact.prevent="finishEdit(note)"
            class="note-editor"
          />
          <!-- Sizing corner -->
          <div class="resizer" @mousedown.stop="startResize(note, $event)"></div>
        </div>
        <div
          v-for="child in children"
          :key="child.id"
          class="board-wrapper"
          @click.stop="(e) => toggleBoardSelection(child, e)"
          :class="['board-wrapper', { selected: selectedBoards.some((b) => b.id === child.id) }]"
          :style="{ left: child.position_x + 'px', top: child.position_y + 'px' }"
          @mousedown.stop="startBoardDrag(child, $event)"
          @contextmenu.prevent="openEmojiMenu($event, child)"
          @dblclick.stop="goToBoard(child.id)"
        >
          <div class="board-card">
            <div class="emoji">{{ child?.emoji }}</div>
          </div>

          <div v-if="!child.editing" class="board-label" @dblclick.stop="startEditTitle(child)">
            {{ child.title }}
          </div>
          <input
            v-else
            class="board-title-input"
            v-model="child.title"
            :ref="(el) => (titleInputs[child.id] = el)"
            @blur="saveBoardTitle(child)"
            @keyup.enter="saveBoardTitle(child)"
            @keyup.esc="cancelEditTitle(child)"
          />
          <div class="board-meta">
            <span>{{ getNoteCount(child.id) }} 📝</span>
            <span>{{ getChildBoardCount(child.id) }} 📁</span>
            <span>{{ getFileCount(child.id) }} 📄</span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
const draggedBoards = ref([])
const boardOffsetMap = new Map()
const titleInputs = {}
const selectedNotes = ref([])
const selectedBoards = ref([])
const allNotes = ref([])
const allBoards = ref([])
const getNoteCount = (id) => allNotes.value.filter((n) => n.board == id).length
const getChildBoardCount = (id) => allBoards.value.filter((b) => b.parent == id).length
const getFileCount = (id) => 0 // majd jön ide a documents szűrés
const draggedNotes = ref([])
const dragOffsetMap = new Map()

import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const router = useRouter()

const goToBoard = (id) => {
  if (route.params.id !== String(id)) {
    router.push(`/boards/${id}`)
  }
}

// 📚 Állapotok
const board = ref({})
const notes = ref([])
const children = ref([])

// 🎨 Színek + ikonok
const availableIcons = [
  '📄',
  '📝',
  '📦',
  '📁',
  '⚙️',
  '✅',
  '🧠',
  '🚀',
  '🎯',
  '🗃️',
  '🗂️',
  '🗄️',
  '💡',
  '✏️',
  '🖋️',
  '📒',
  '🧾',
  '📌',
  '📅',
  '📈',
  '⏳',
  '🔁',
  '🕒',
  '☑️',
  '🔒',
  '📥',
  '📤',
  '🎨',
  '🌈',
  '🧱',
  '🧩',
  '🔧',
  '🧰',
  '🖥️',
]

// 📌 Snap to grid
const gridSize = 20
const snapToGrid = (value) => Math.round(value / gridSize) * gridSize

const toggleNoteSelection = (note, event) => {
  const isMulti = event.ctrlKey || event.metaKey // 💡 Windows: Ctrl, Mac: Cmd

  if (isMulti) {
    const exists = selectedNotes.value.some((n) => n.id === note.id)
    if (exists) {
      selectedNotes.value = selectedNotes.value.filter((n) => n.id !== note.id)
    } else {
      selectedNotes.value.push(note)
    }
    selectedBoards.value = []
  } else {
    selectedNotes.value = [note]
    selectedBoards.value = []
  }
}

const toggleBoardSelection = (board, event) => {
  if (!board || typeof board !== 'object') return

  const isMulti = event.ctrlKey || event.metaKey

  if (isMulti) {
    const exists = selectedBoards.value.some((b) => b.id === board.id)
    if (exists) {
      selectedBoards.value = selectedBoards.value.filter((b) => b.id !== board.id)
    } else {
      selectedBoards.value.push(board)
    }
    // Jegyzeteket nem törlünk
  } else {
    selectedBoards.value = [board]
    selectedNotes.value = []
  }
}


const startEditTitle = (child) => {
  children.value.forEach((b) => (b.editing = false))
  child.editing = true
  nextTick(() => {
    const el = titleInputs[child.id]
    if (el) {
      el.focus()
      el.select() // 🔥 ez jelöli ki a teljes szöveget
    }
  })
}

const saveBoardTitle = async (child) => {
  child.editing = false
  await axios.patch(`http://127.0.0.1:8000/api/boards/${child.id}/`, {
    title: child.title,
  })
}

const cancelEditTitle = (child) => {
  child.editing = false
  // opcionálisan visszaállíthatod az eredeti címet is, ha elmented előtte
}

// 📍 Emoji menü jobb klikkre
const emojiMenu = ref({
  visible: false,
  x: 0,
  y: 0,
  board: null,
})
onMounted(async () => {
  await fetchBoardWithAncestors(route.params.id)

  const notesRes = await axios.get('http://127.0.0.1:8000/api/notes/')
  notes.value = notesRes.data
    .filter((n) => n.board === board.value.id)
    .map((n) => ({ ...n, editing: false }))

  const boardsRes = await axios.get('http://127.0.0.1:8000/api/boards/')
  children.value = boardsRes.data.filter((b) => b.parent === board.value.id)

  window.addEventListener('keydown', handleKeyDown)
  console.log('Notes:', notes.value)
  console.log('Children:', children.value)
})

onMounted(async () => {
  console.log('children:', children.value)
  await fetchBoardWithAncestors(route.params.id)
  window.addEventListener('keydown', handleKeyDown)
  window.addEventListener('click', handleGlobalClick)
})

const boardAncestors = ref([])

const fetchBoardWithAncestors = async (id) => {
  boardAncestors.value = []
  let currentId = id

  while (currentId) {
    const res = await axios.get(`http://127.0.0.1:8000/api/boards/${currentId}/`)
    const data = res.data
    boardAncestors.value.unshift(data)
    currentId = data.parent
  }

  // Az aktuális board az utolsó a sorban
  board.value = boardAncestors.value.at(-1)

  // 👇 Duplikált vég-elem kiszűrése (ha a board szülője is ő maga)
  const lastTwo = boardAncestors.value.slice(-2)
  if (lastTwo.length === 2 && lastTwo[0].id === lastTwo[1].id) {
    boardAncestors.value.pop()
  }

  // Jegyzetek & gyermek boardok betöltése
  const notesRes = await axios.get('http://127.0.0.1:8000/api/notes/')
  notes.value = notesRes.data
    .filter((n) => n.board === board.value.id)
    .map((n) => ({ ...n, editing: false }))

  const boardsRes = await axios.get('http://127.0.0.1:8000/api/boards/')
  children.value = boardsRes.data.filter((b) => b.parent === board.value.id)

  const allNotesRes = await axios.get('http://127.0.0.1:8000/api/notes/')
  allNotes.value = allNotesRes.data.map((n) => ({ ...n, editing: false }))

  const allBoardsRes = await axios.get('http://127.0.0.1:8000/api/boards/')
  allBoards.value = allBoardsRes.data

  // Az aktuális board tartalma
  notes.value = allNotes.value.filter((n) => n.board == board.value.id)

  children.value = allBoards.value
    .filter((b) => b.parent == board.value.id && b.id !== board.value.id)
    .map((b) => ({ ...b, editing: false }))
}

onBeforeUnmount(() => {
  window.removeEventListener('click', handleGlobalClick)
})

const handleGlobalClick = (e) => {
  const isInsideNoteOrBoard =
    e.target.closest('.sticky-note') ||
    e.target.closest('.sticky-note *') ||
    e.target.closest('.board-wrapper') ||
    e.target.closest('.board-wrapper *')
  const isInsideToolbar = e.target.closest('.toolbar')

  if (!isInsideNoteOrBoard && !isInsideToolbar) {
    selectedNotes.value = []
    selectedBoards.value = []
  }
}

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeyDown)
})

const handleKeyDown = async (e) => {
  if (e.key === 'Delete') {
    if (selectedNotes.value.length) {
      const confirmDelete = confirm(`Biztosan törlöd a ${selectedNotes.value.length} jegyzetet?`)
      if (!confirmDelete) return
      for (const note of selectedNotes.value) {
        await axios.delete(`http://127.0.0.1:8000/api/notes/${note.id}/`)
      }
      notes.value = notes.value.filter((n) => !selectedNotes.value.includes(n))
      selectedNotes.value = []
    } else if (selectedBoards.value.length) {
      const confirmDelete = confirm(`Biztosan törlöd a ${selectedBoards.value.length} boardot?`)
      if (!confirmDelete) return
      for (const board of selectedBoards.value) {
        await axios.delete(`http://127.0.0.1:8000/api/boards/${board.id}/`)
      }
      children.value = children.value.filter((b) => !selectedBoards.value.includes(b))
      selectedBoards.value = []
    }
  }
}

const createNote = async () => {
  const res = await axios.post('http://127.0.0.1:8000/api/notes/', {
    board: board.value.id,
    content: 'Új jegyzet',
    position_x: snapToGrid(100),
    position_y: snapToGrid(100),
    background_color: '#fff8b3',
    text_color: '#000000',
    width: 160,
    height: 100,
  })
  notes.value.push({ ...res.data, editing: true })
}
const hasMixedColors = computed(() => {
  if (selectedNotes.value.length <= 1) return false
  const base = selectedNotes.value[0].background_color
  return selectedNotes.value.some((n) => n.background_color !== base)
})

const createBoard = async () => {
  const res = await axios.post('http://127.0.0.1:8000/api/boards/', {
    title: 'Új board',
    parent: board.value.id || null,
    user: board.value.user,
    emoji: '📁',
    position_x: snapToGrid(200),
    position_y: snapToGrid(150),
  })
  children.value.push(res.data)
}

const createDocument = async () => {
  await axios.post('http://127.0.0.1:8000/api/documents/', {
    board: board.value.id,
    title: 'Új dokumentum',
    content: '',
  })
  alert('📄 Új dokumentum létrehozva!')
}

const updateNoteStyle = async (note) => {
  await axios.patch(`http://127.0.0.1:8000/api/notes/${note.id}/`, {
    background_color: note.background_color,
    text_color: note.text_color,
  })
}

const updateBoardIcon = async (boardObj, icon) => {
  boardObj.emoji = icon
  await axios.patch(`http://127.0.0.1:8000/api/boards/${boardObj.id}/`, {
    emoji: icon,
  })
}
// 🎯 Jegyzet mozgatás (egérrel)
const draggedNote = ref(null)
const offset = { x: 0, y: 0 }

const startDrag = (note, e) => {
  draggedNotes.value = selectedNotes.value.length > 0 ? [...selectedNotes.value] : [note]

  dragOffsetMap.clear()
  for (const n of draggedNotes.value) {
    dragOffsetMap.set(n.id, {
      x: e.clientX - n.position_x,
      y: e.clientY - n.position_y,
    })
  }

  window.addEventListener('mousemove', onDrag)
  window.addEventListener('mouseup', stopDrag)
}

const onDrag = (e) => {
  for (const note of draggedNotes.value) {
    const offset = dragOffsetMap.get(note.id)
    if (!offset) continue
    note.position_x = snapToGrid(e.clientX - offset.x)
    note.position_y = snapToGrid(e.clientY - offset.y)
  }
}

const stopDrag = async () => {
  for (const note of draggedNotes.value) {
    await axios.patch(`http://127.0.0.1:8000/api/notes/${note.id}/`, {
      position_x: note.position_x,
      position_y: note.position_y,
    })
  }
  draggedNotes.value = []
  dragOffsetMap.clear()
  window.removeEventListener('mousemove', onDrag)
  window.removeEventListener('mouseup', stopDrag)
}

// 📁 Board mozgatás (ugyanez boardokra)
let draggedBoard = null
let boardOffset = { x: 0, y: 0 }

const startBoardDrag = (board, e) => {
  draggedBoards.value =
    selectedBoards.value.length > 0 ? [...selectedBoards.value] : [board]

  boardOffsetMap.clear()
  for (const b of draggedBoards.value) {
    boardOffsetMap.set(b.id, {
      x: e.clientX - b.position_x,
      y: e.clientY - b.position_y,
    })
  }

  window.addEventListener('mousemove', onBoardDrag)
  window.addEventListener('mouseup', stopBoardDrag)
}

const onBoardDrag = (e) => {
  for (const board of draggedBoards.value) {
    const offset = boardOffsetMap.get(board.id)
    if (!offset) continue
    board.position_x = snapToGrid(e.clientX - offset.x)
    board.position_y = snapToGrid(e.clientY - offset.y)
  }
}


const stopBoardDrag = async () => {
  for (const board of draggedBoards.value) {
    await axios.patch(`http://127.0.0.1:8000/api/boards/${board.id}/`, {
      position_x: board.position_x,
      position_y: board.position_y,
    })
  }

  draggedBoards.value = []
  boardOffsetMap.clear()
  window.removeEventListener('mousemove', onBoardDrag)
  window.removeEventListener('mouseup', stopBoardDrag)
}

// 🧲 Jegyzet áthelyezése másik board-ra
const handleNoteDropOnBoard = async (e, targetBoard) => {
  if (!draggedNote.value || !targetBoard) return
  await axios.patch(`http://127.0.0.1:8000/api/notes/${draggedNote.value.id}/`, {
    board: targetBoard.id,
  })
  notes.value = notes.value.filter((n) => n.id !== draggedNote.value.id)
  draggedNote.value = null
}

// 🖊️ Szerkesztés dupla kattintásra
const finishEdit = async (note) => {
  note.editing = false
  await axios.patch(`http://127.0.0.1:8000/api/notes/${note.id}/`, {
    content: note.content,
  })
}

// ↔️ Jegyzet méretezése
const startResize = (note, e) => {
  const startX = e.clientX
  const startY = e.clientY
  const startWidth = note.width || 160
  const startHeight = note.height || 100

  const onMouseMove = (ev) => {
    note.width = Math.max(100, startWidth + (ev.clientX - startX))
    note.height = Math.max(80, startHeight + (ev.clientY - startY))
  }

  const onMouseUp = async () => {
    window.removeEventListener('mousemove', onMouseMove)
    window.removeEventListener('mouseup', onMouseUp)
    await axios.patch(`http://127.0.0.1:8000/api/notes/${note.id}/`, {
      width: note.width,
      height: note.height,
    })
  }

  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
}

// ⌨️ Bezárás ESC-re
window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    emojiMenu.value.visible = false
  }
})

const openSettings = () => {
  alert('⚙️ Beállítások még nincsenek – de dolgozhatunk rajta 😄')
}

watch(
  () => route.params.id,
  async (newId) => {
    await fetchBoardWithAncestors(newId)
    selectedNotes.value = []
    selectedBoards.value = []
  },
)
</script>

<style scoped>
.icon-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: center;
  padding: 6px;
  overflow-y: auto;

  border-top: 1px solid #ccc;
}
.icon-picker::-webkit-scrollbar {
  width: 6px;
}
.icon-picker::-webkit-scrollbar-thumb {
  background-color: #bbb;
  border-radius: 3px;
}
.emoji-option {
  font-size: 22px;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  transition: background 0.2s;
}

.emoji-option.selected {
  background-color: #ccc;
  box-shadow: inset 0 0 2px #888;
}
.sticky-note {
  position: absolute;
  min-width: 100px;
  min-height: 80px;
  padding: 8px;
  border-radius: 6px;
  box-shadow: 2px 2px 6px rgba(0, 0, 0, 0.15);
  cursor: grab;
  user-select: none;
  overflow: hidden;
  border: 1px solid transparent;
}
.resizer {
  position: absolute;
  width: 16px;
  height: 16px;
  right: 2px;
  bottom: 2px;
  background: transparent;
  border-right: 2px solid rgba(0, 0, 0, 0.3);
  border-bottom: 2px solid rgba(0, 0, 0, 0.3);
  box-sizing: border-box;
  cursor: nwse-resize;
  pointer-events: auto;
}
.topbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 40px;
  background: #fdfdfd;
  border-bottom: 1px solid #ccc;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: bold;
  font-size: 15px;
  z-index: 1000;
}
.emoji-panel {
  position: fixed;
  top: 60px;
  right: 16px;
  background: #fff;
  border: 1px solid #ccc;
  border-radius: 10px;
  padding: 12px 16px;
  width: 180px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.emoji-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.emoji-grid span {
  font-size: 24px;
  cursor: pointer;
  padding: 6px;
  border-radius: 6px;
  transition: background 0.2s;
}

.emoji-grid span.selected {
  background: #f0f0f0;
  box-shadow: inset 0 0 0 2px #666;
}

.topbar-left {
  color: #333;
}
.board-meta {
  margin-top: 2px;
  font-size: 11px;
  color: #666;
  text-align: center;
  display: flex;
  gap: 6px;
  justify-content: center;
  flex-wrap: wrap;
  user-select: none;
}

.note-editor {
  width: 100%;
  height: 100%;
  border: none;
  outline: none;
  resize: none;
  font: inherit;
  background: transparent;
  padding: 0;
  box-sizing: border-box;
}

.topbar-right {
  display: flex;
  align-items: center;
}
.settings-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  padding: 4px;
  transition: transform 0.2s;
}
.settings-btn:hover {
  transform: rotate(20deg);
}
.board-area {
  flex: 1;
  position: relative;
  height: calc(100vh - 40px);
  margin-top: 40px;
  /* Ezzel elkerülöd az átfedést */
  overflow: hidden;
  margin-left: 48px;
}
.toolbar {
  position: fixed;
  top: 40px;
  left: 0;
  width: 48px;
  height: calc(100vh - 40px);
  background: #f8f8f8;
  padding: 0px 4px;
  border-right: 1px solid #ccc;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  z-index: 999;
}
.toolbar button {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  transition: transform 0.2s;
}
.toolbar button:hover {
  transform: scale(1.2);
}
.color-tools {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 8px;
}
.color-tools input[type='color'] {
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 4px;
  padding: 0;
  cursor: pointer;
  box-shadow: 0 0 3px rgba(0, 0, 0, 0.2);
}
.board-card {
  border-radius: 8px;
  background: #f8f8f8;
  border: 1px solid #ccc;
  box-shadow: 1px 1px 5px rgba(0, 0, 0, 0.1);
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
  cursor: grab;
  user-select: none;
  display: flex;
  flex-direction: column;
}
.board-title-input {
  font-size: 11px;
  text-align: center;
  color: #444;
  border: 1px solid #ccc;
  border-radius: 4px;
  width: 100%;
  padding: 4px 2px;
  box-sizing: border-box;
}

.emoji {
  font-size: 36px;
  text-align: center;
}
.template-icon {
  font-size: 28px;
  cursor: grab;
  margin: 10px 0;
  transition: transform 0.2s;
}
.template-icon:hover {
  transform: scale(1.2);
}
.board-title-small {
  font-size: 11px;
  text-align: center;
  color: #444;
  padding-top: 2px;
  white-space: nowrap;
  text-overflow: ellipsis;
  max-width: 100%;
  user-select: none;
}
.board-wrapper {
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 80px;
  pointer-events: auto;
  min-height: 100px; /* vagy nagyobb, ha kell */
  z-index: 1;
  min-height: 120px;
}
.board-wrapper.selected .board-card {
  border-color: #00000067;
  box-shadow: 0 0 4px 2px rgb(255, 255, 255);
}
input.mixed {
  outline: 2px dashed orange;
  opacity: 0.7;
}

.board-card {
  width: 65px;
  height: 65px;
  background: #fff;
  border: 2px solid #ccc;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.board-label {
  margin-top: 4px;
  font-size: 11px;
  text-align: center;
  color: #444;
  white-space: nowrap;
  text-overflow: ellipsis;
  max-width: 100%;
  user-select: none;
}
.breadcrumb-link {
  font-weight: 500;
  font-size: 16px;
  color: #333;
  transition: color 0.2s;
}
.breadcrumb-link:hover {
  color: #007bff;
}
.sticky-note.selected {
  outline: 2px solid #00000067;
  outline-offset: -1px;
  box-shadow: 0 0 4px 2px rgb(255, 255, 255);
}
.sticky-note.selected {
  outline: 2px solid #007bff;
}
.board-wrapper.selected .board-card {
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.3);
}
.sticky-note.dragging {
  opacity: 0.7;
  cursor: grabbing;
}
</style>
