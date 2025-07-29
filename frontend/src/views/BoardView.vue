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
    <div style="flex: 1; padding-left: 16px" @mousedown="startLasso" ref="boardArea">
      <section>
        <svg class="lasso-box" v-if="isLassoing">
          <rect
            :x="lassoRect.x"
            :y="lassoRect.y"
            :width="lassoRect.width"
            :height="lassoRect.height"
          />
        </svg>
        <div
          v-for="note in notes"
          :key="note.id"
          class="sticky-note"
          :class="{
            selected: selectedNotes.some((n) => n.id === note.id),
            dragging: draggedNotes.some((n) => n.id === note.id),
          }"
          :style="{
            left: note.position_x + 'px',
            top: note.position_y + 'px',
            background: note.background_color,
            color: note.text_color,
            width: note.width + 'px',
            height: note.height + 'px',
            borderColor: note.background_color,
          }"
          @mousedown.stop="startUnifiedDrag(note, $event)"
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
          :class="[
            'board-wrapper',
            {
              selected: selectedBoards.some((b) => b.id === child.id),
              dragging: draggedBoards.some((b) => b.id === child.id),
            },
          ]"
          @click.stop="(e) => toggleBoardSelection(child, e)"
          :style="{ left: child.position_x + 'px', top: child.position_y + 'px' }"
          @mousedown.stop="startUnifiedDrag(child, $event)"
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
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useApi } from '@/composables/useApi'

// — ROUTER —
const route = useRoute()
const router = useRouter()
const api = useApi()
const goToBoard = (id) => {
  if (route.params.id !== String(id)) {
    router.push(`/boards/${id}`)
  }
}

// — ÁLLAPOTOK & REFS —
const boardAncestors = ref([])
const board = ref({})
const boardArea = ref(null)
const allNotes = ref([])
const allBoards = ref([])

const notes = computed(() => allNotes.value.filter((n) => n.board === board.value.id))
const children = computed(() =>
  allBoards.value.filter((b) => b.parent === board.value.id && b.id !== board.value.id),
)

const selectedNotes = ref([])
const selectedBoards = ref([])
const draggedNotes = ref([])
const draggedBoards = ref([])
const dragHappened = ref(false)

const dragOffsetMap = new Map()
const boardOffsetMap = new Map()
const titleInputs = {} // ref-ek a board-cím inputokhoz
const emojiMenu = ref({ visible: false, x: 0, y: 0, board: null })
const isLassoing = ref(false)
const lassoStart = ref({ x: 0, y: 0 })
const lassoEnd = ref({ x: 0, y: 0 })

// — KONSTANSOK & HELPEREK —
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
const gridSize = 20
const snapToGrid = (v) => Math.round(v / gridSize) * gridSize

const hasMixedColors = computed(() => {
  if (selectedNotes.value.length < 2) return false
  const base = selectedNotes.value[0].background_color
  return selectedNotes.value.some((n) => n.background_color !== base)
})

const lassoRect = computed(() => {
  if (!isLassoing.value) return { x: 0, y: 0, width: 0, height: 0 }
  const x = Math.min(lassoStart.value.x, lassoEnd.value.x)
  const y = Math.min(lassoStart.value.y, lassoEnd.value.y)
  const width = Math.abs(lassoStart.value.x - lassoEnd.value.x)
  const height = Math.abs(lassoStart.value.y - lassoEnd.value.y)
  return { x, y, width, height }
})

// — TEMPLATE‐HELPEREK —
const getNoteCount = (id) => allNotes.value.filter((n) => n.board === id).length

const getChildBoardCount = (id) => allBoards.value.filter((b) => b.parent === id).length

const getFileCount = () => 0 // majd docs‐számítás

// — KIJELÖLÉS —
function toggleNoteSelection(note, e) {
  if (dragHappened.value) {
    dragHappened.value = false
    return
  }
  const isMulti = e.ctrlKey || e.metaKey
  const exists = selectedNotes.value.some((n) => n.id === note.id)

  if (isMulti) {
    selectedNotes.value = exists
      ? selectedNotes.value.filter((n) => n.id !== note.id)
      : [...selectedNotes.value, note]
  } else {
    selectedNotes.value = [note]
    selectedBoards.value = []
  }
}

function toggleBoardSelection(brd, e) {
  if (dragHappened.value) {
    dragHappened.value = false
    return
  }
  const isMulti = e.ctrlKey || e.metaKey
  const exists = selectedBoards.value.some((b) => b.id === brd.id)

  if (isMulti) {
    selectedBoards.value = exists
      ? selectedBoards.value.filter((b) => b.id !== brd.id)
      : [...selectedBoards.value, brd]
  } else {
    selectedBoards.value = [brd]
    selectedNotes.value = []
  }
}

function startLasso(e) {
  // Csak akkor induljon a lasszó, ha a háttérre kattintunk
  if (e.target.closest('.sticky-note, .board-wrapper')) {
    return
  }

  isLassoing.value = true
  const rect = boardArea.value.getBoundingClientRect()
  lassoStart.value = { x: e.clientX - rect.left, y: e.clientY - rect.top }
  lassoEnd.value = { ...lassoStart.value }

  // Kezdetben töröljük a kijelölést, ha nem használunk multi-select modifiert
  if (!e.ctrlKey && !e.metaKey) {
    selectedNotes.value = []
    selectedBoards.value = []
  }

  window.addEventListener('mousemove', onLasso)
  window.addEventListener('mouseup', stopLasso, { once: true })
}

function onLasso(e) {
  if (!isLassoing.value) return
  const rect = boardArea.value.getBoundingClientRect()
  lassoEnd.value = {
    x: e.clientX - rect.left,
    y: e.clientY - rect.top,
  }
  updateSelectionWithLasso()
}

function stopLasso() {
  isLassoing.value = false
  window.removeEventListener('mousemove', onLasso)
}

function updateSelectionWithLasso() {
  const lasso = lassoRect.value
  const newSelectedNotes = []
  const newSelectedBoards = []

  notes.value.forEach((note) => {
    const itemRect = {
      x: note.position_x,
      y: note.position_y,
      width: note.width,
      height: note.height,
    }
    if (rectsIntersect(lasso, itemRect)) {
      newSelectedNotes.push(note)
    }
  })

  children.value.forEach((board) => {
    const itemRect = {
      x: board.position_x,
      y: board.position_y,
      width: 80, // board-wrapper width
      height: 120, // board-wrapper min-height
    }
    if (rectsIntersect(lasso, itemRect)) {
      newSelectedBoards.push(board)
    }
  })

  selectedNotes.value = newSelectedNotes
  selectedBoards.value = newSelectedBoards
}

function rectsIntersect(r1, r2) {
  return !(
    r2.x > r1.x + r1.width ||
    r2.x + r2.width < r1.x ||
    r2.y > r1.y + r1.height ||
    r2.y + r2.height < r1.y
  )
}

// — CRUD: LÉTREHOZÁS —
async function createNote() {
  const res = await api.createResource('notes/', {
    board: board.value.id,
    content: 'Új jegyzet',
    position_x: snapToGrid(100),
    position_y: snapToGrid(100),
    background_color: '#fff8b3',
    text_color: '#000000',
    width: 160,
    height: 100,
  })
  allNotes.value.push({ ...res, editing: true })
}

async function createBoard() {
  const res = await api.createResource('boards/', {
    title: 'Új board',
    parent: board.value.id || null,
    user: board.value.user,
    emoji: '📁',
    position_x: snapToGrid(200),
    position_y: snapToGrid(150),
  })
  allBoards.value.push({ ...res, editing: false })
}

async function finishEdit(note) {
  note.editing = false
  await api.updateResource(`notes/${note.id}/`, { content: note.content })
}

async function createDocument() {
  await api.createResource('documents/', {
    board: board.value.id,
    title: 'Új dokumentum',
    content: '',
  })
  alert('📄 Új dokumentum létrehozva!')
}

// — CRUD: FRISSÍTÉS —
async function updateNoteStyle(note) {
  await api.updateResource(`notes/${note.id}/`, {
    background_color: note.background_color,
    text_color: note.text_color,
  })
}

async function updateBoardIcon(brd, icon) {
  brd.emoji = icon
  await api.updateResource(`boards/${brd.id}/`, { emoji: icon })
}

function startUnifiedDrag(item, e) {
  // Detect a note by the presence of `content`
  const isNote = 'content' in item

  // Check if this item is already in the current selection
  const inSelection = isNote
    ? selectedNotes.value.some((n) => n.id === item.id)
    : selectedBoards.value.some((b) => b.id === item.id)

  // If it isn’t selected, bail out and let your click handler do its thing
  if (!inSelection) {
    dragHappened.value = false
    return
  }

  dragHappened.value = true
  draggedNotes.value = [...selectedNotes.value]
  draggedBoards.value = [...selectedBoards.value]

  dragOffsetMap.clear()
  boardOffsetMap.clear()

  const { left, top } = boardArea.value.getBoundingClientRect()

  // Build up offsets for notes
  draggedNotes.value.forEach((n) => {
    dragOffsetMap.set(n.id, {
      x: e.clientX - left - n.position_x,
      y: e.clientY - top - n.position_y,
    })
  })

  // Build up offsets for boards
  draggedBoards.value.forEach((b) => {
    boardOffsetMap.set(b.id, {
      x: e.clientX - left - b.position_x,
      y: e.clientY - top - b.position_y,
    })
  })

  window.addEventListener('mousemove', onUnifiedDrag)
  window.addEventListener('mouseup', stopUnifiedDrag, { once: true })
}

function onUnifiedDrag(e) {
  dragHappened.value = true
  draggedNotes.value.forEach((n) => {
    const off = dragOffsetMap.get(`note-${n.id}`)
    if (!off) return
    n.position_x = snapToGrid(e.clientX - off.x)
    n.position_y = snapToGrid(e.clientY - off.y)
  })
  draggedBoards.value.forEach((b) => {
    const off = boardOffsetMap.get(b.id)
    if (!off) return
    b.position_x = snapToGrid(e.clientX - off.x)
    b.position_y = snapToGrid(e.clientY - off.y)
  })
}

async function stopUnifiedDrag() {
  await Promise.all([
    ...draggedNotes.value.map((n) =>
      api.updateResource(`notes/${n.id}/`, {
        position_x: n.position_x,
        position_y: n.position_y,
      }),
    ),
    ...draggedBoards.value.map((b) =>
      api.updateResource(`boards/${b.id}/`, {
        position_x: b.position_x,
        position_y: b.position_y,
      }),
    ),
  ])

  draggedNotes.value.length = 0
  draggedBoards.value.length = 0
  dragOffsetMap.clear()
  boardOffsetMap.clear()

  window.removeEventListener('mousemove', onUnifiedDrag)
  window.removeEventListener('mouseup', stopUnifiedDrag)
}

// — BILLENTYŰZET & GLOBÁLIS KLIKK —
async function handleKeyDown(e) {
  if (e.key !== 'Delete') return
  const total = selectedNotes.value.length + selectedBoards.value.length
  if (!total || !confirm(`Biztos törlöd a ${total} elemet?`)) return

  await Promise.all([
    ...selectedNotes.value.map((n) => api.deleteResource(`notes/${n.id}/`)),
    ...selectedBoards.value.map((b) => api.deleteResource(`boards/${b.id}/`)),
  ])

  allNotes.value = allNotes.value.filter((n) => !selectedNotes.value.includes(n))
  allBoards.value = allBoards.value.filter((b) => !selectedBoards.value.includes(b))
  selectedNotes.value.length = 0
  selectedBoards.value.length = 0
}

function handleGlobalClick(e) {
  const inside = e.target.closest(
    '.sticky-note, .sticky-note *, .board-wrapper, .board-wrapper *, .toolbar',
  )
  if (!inside) {
    selectedNotes.value.length = 0
    selectedBoards.value.length = 0
  }
}

// — ESC & SETTINGS —
function onKeyDownEsc(e) {
  if (e.key === 'Escape') emojiMenu.value.visible = false
}

function openSettings() {
  alert('⚙️ Beállítások még nincsenek – dolgozhatunk rajta 😊')
}

// — BETÖLTÉS & ŐRZÉS —
async function fetchBoardWithAncestors(id) {
  boardAncestors.value = []
  let cur = id
  while (cur) {
    const boardData = await api.fetchResource(`boards/${cur}/`)
    boardAncestors.value.unshift(boardData)
    cur = boardData.parent
  }
  // dupla végpont kiszűrése
  if (boardAncestors.value.length > 1) {
    const lastTwo = boardAncestors.value.slice(-2)
    if (lastTwo[0].id === lastTwo[1].id) boardAncestors.value.pop()
  }
  board.value = boardAncestors.value.at(-1) || {}
}

onMounted(async () => {
  await fetchBoardWithAncestors(route.params.id)
  const [notesData, boardsData] = await Promise.all([
    api.fetchResource('notes/'),
    api.fetchResource('boards/'),
  ])
  allNotes.value = notesData.map((n) => ({ ...n, editing: false }))
  allBoards.value = boardsData.map((b) => ({ ...b, editing: false }))

  window.addEventListener('keydown', handleKeyDown)
  window.addEventListener('keydown', onKeyDownEsc)
  window.addEventListener('click', handleGlobalClick)
  window.addEventListener('keydown', onKeyDownGlobal)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeyDown)
  window.removeEventListener('keydown', onKeyDownEsc)
  window.removeEventListener('click', handleGlobalClick)
  window.removeEventListener('keydown', onKeyDownGlobal)
})

watch(
  () => route.params.id,
  async (newId) => {
    await fetchBoardWithAncestors(newId)
    selectedNotes.value.length = 0
    selectedBoards.value.length = 0
  },
)
function onKeyDownGlobal(e) {
  // törléseddel már van handleKeyDown: kiegészítjük
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'a') {
    e.preventDefault()
    // minden jegyzet és board
    selectedNotes.value = [...notes.value]
    selectedBoards.value = [...children.value]
  }
}
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
.board-wrapper.dragging {
  opacity: 0.7;
  cursor: grabbing;
}
.lasso-box {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 100;
}

.lasso-box rect {
  fill: rgba(0, 123, 255, 0.2);
  stroke: rgba(0, 123, 255, 0.8);
  stroke-width: 1px;
}
</style>
