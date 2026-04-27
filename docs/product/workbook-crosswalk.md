# Workbook Crosswalk

## Source

- Frozen workbook input: `/home/yehor/Work/annotation_tool/docs/Annotation tool FR.xlsx`
- Sheet coverage: `Sheet1`
- Row coverage in this pass: 197 workbook rows
- Amendment rule: revise entries only by amendment so original dispositions remain visible in history

## First-Pass Disposition Note

The initial Phase 1 mapping was traceability-first: every workbook row was first mapped into a Markdown workflow/requirement bucket instead of being left untracked. ADR `0003` records the first semantic disposition pass on top of that baseline.

In this document, `adopted` means "mapped into the Markdown requirement set for follow-up review", not "fully approved with no remaining ambiguity." Requirement tags, ADRs, and later crosswalk amendments still carry unresolved conflicts or missing product intent.

## Disposition Rules

- `adopted`: mapped into a first-pass Markdown requirement ID
- `rejected`: intentionally not carried forward, with rationale
- `deferred`: not accepted for release scope yet and requires follow-up owner/date later
- `superseded`: replaced by a later ADR

## Workbook Coverage Gaps

The frozen workbook does not contain dedicated event-validation workflow rows in this first-pass mapping. The only workbook references to event validation are:

- `FR-009`, which lists event validation as a supported annotation mode,
- `FR-010`, which lists event-validation-related stages in the global stage list.

ADR `0007` originally deferred event validation from the first PySide release. That decision is superseded on 2026-04-24 for the Linux PySide scope:

- `FR-009` and `FR-010` include the event-validation mode/stage arms in Linux PySide scope.
- `WF-EVAL-ANSWER`, `WF-EVAL-VIEW`, and `WF-EVAL-OVERWRITE` (and their `REQ-EVAL-*` requirements) are active PySide requirements for Linux.
- `EVENT_VALIDATION` projects opened in PySide must route to a PySide event-validation screen, not a deferral dialog.

## Crosswalk Entries

| Workbook ID | Category | Subcategory | Severity | Workbook summary | Disposition | Workflow ID | Requirement ID | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FR-122 | Canvas і перегляд | Zoom/pan/fit/navigation viewport | 1 | Canvas має підтримувати zoom колесом миші. | adopted | WF-CANV-VIEWPORT | REQ-CANV-VIEWPORT-001 |  |
| FR-125 | Canvas і перегляд | Zoom/pan/fit/navigation viewport | 1 | Canvas має автоматично fit image при зміні frame/image, якщо відповідний режим активний. | adopted | WF-CANV-VIEWPORT | REQ-CANV-VIEWPORT-001 |  |
| FR-085 | Canvas і перегляд | Перемикання visibility/render modes |  | Користувач може перемикати visibility label names. | adopted | WF-CANV-RENDER | REQ-CANV-RENDER-001 |  |
| FR-086 | Canvas і перегляд | Перемикання visibility/render modes |  | Користувач може перемикати visibility object size. | adopted | WF-CANV-RENDER | REQ-CANV-RENDER-001 |  |
| FR-087 | Canvas і перегляд | Перемикання visibility/render modes |  | Користувач може перемикати hiding figures. | adopted | WF-CANV-RENDER | REQ-CANV-RENDER-001 |  |
| FR-088 | Canvas і перегляд | Перемикання visibility/render modes |  | Користувач може перемикати hiding review labels. | adopted | WF-CANV-RENDER | REQ-CANV-RENDER-001 |  |
| FR-118 | Canvas і перегляд | Перемикання visibility/render modes |  | Для blur label застосунок має розмивати відповідну область image. | adopted | WF-CANV-RENDER | REQ-CANV-RENDER-001 |  |
| FR-119 | Canvas і перегляд | Перемикання visibility/render modes |  | Blur має працювати через downscale/upscale preview image і mask області. | adopted | WF-CANV-RENDER | REQ-CANV-RENDER-001 |  |
| FR-120 | Canvas і перегляд | Перемикання visibility/render modes |  | Користувач може перемикати degraded image preview. | adopted | WF-CANV-RENDER | REQ-CANV-RENDER-001 |  |
| FR-121 | Canvas і перегляд | Перемикання visibility/render modes |  | Degraded image preview має blur + зменшену saturation. | adopted | WF-CANV-RENDER | REQ-CANV-RENDER-001 |  |
| FR-123 | Canvas і перегляд | Zoom/pan/fit/navigation viewport |  | Canvas має підтримувати pan правою кнопкою миші. | adopted | WF-CANV-VIEWPORT | REQ-CANV-VIEWPORT-001 |  |
| FR-124 | Canvas і перегляд | Zoom/pan/fit/navigation viewport |  | Canvas має підтримувати fit image to window. | adopted | WF-CANV-VIEWPORT | REQ-CANV-VIEWPORT-001 |  |
| FR-126 | Canvas і перегляд | Zoom/pan/fit/navigation viewport |  | Canvas має конвертувати screen coordinates у image coordinates. | adopted | WF-CANV-VIEWPORT | REQ-CANV-VIEWPORT-001 |  |
| FR-127 | Canvas і перегляд | Zoom/pan/fit/navigation viewport |  | Canvas має clamp coordinates до меж image. | adopted | WF-CANV-VIEWPORT | REQ-CANV-VIEWPORT-001 |  |
| FR-128 | Canvas і перегляд | Рендеринг canvas |  | Canvas має оновлювати preview при mouse hover/move/release/press. | adopted | WF-CANV-RENDER | REQ-CANV-RENDER-001 |  |
| FR-129 | Canvas і перегляд | Mouse interactions |  | Canvas має підтримувати left mouse press для створення, вибору або редагування figure. | adopted | WF-CANV-INPUT | REQ-CANV-INPUT-001 |  |
| FR-130 | Canvas і перегляд | Mouse interactions |  | Canvas має підтримувати left mouse move для редагування active figure. | adopted | WF-CANV-INPUT | REQ-CANV-INPUT-001 |  |
| FR-131 | Canvas і перегляд | Mouse interactions |  | Canvas має підтримувати left mouse release для завершення movement/edit operation. | adopted | WF-CANV-INPUT | REQ-CANV-INPUT-001 |  |
| FR-132 | Canvas і перегляд | Keyboard interactions загальні |  | Користувач може перемикатися на наступний item клавішами w або p. | adopted | WF-CANV-INPUT | REQ-CANV-INPUT-001 |  |
| FR-133 | Canvas і перегляд | Keyboard interactions загальні |  | Користувач може перемикатися на попередній item клавішами q або o. | adopted | WF-CANV-INPUT | REQ-CANV-INPUT-001 |  |
| FR-134 | Canvas і перегляд | Keyboard interactions загальні |  | Користувач може fit image клавішею f. | adopted | WF-CANV-INPUT | REQ-CANV-INPUT-001 |  |
| FR-135 | Canvas і перегляд | Keyboard interactions загальні |  | Користувач може undo через Ctrl/Cmd+Z. | adopted | WF-CANV-INPUT | REQ-CANV-INPUT-001 |  |
| FR-136 | Canvas і перегляд | Keyboard interactions загальні |  | Користувач може redo через Ctrl/Cmd+Y. | adopted | WF-CANV-INPUT | REQ-CANV-INPUT-001 |  |
| FR-137 | Canvas і перегляд | Keyboard interactions загальні |  | Користувач може copy через Ctrl/Cmd+C. | adopted | WF-CANV-INPUT | REQ-CANV-INPUT-001 |  |
| FR-138 | Canvas і перегляд | Keyboard interactions загальні |  | Користувач може paste через Ctrl/Cmd+V. | adopted | WF-CANV-INPUT | REQ-CANV-INPUT-001 |  |
| FR-143 | Canvas і перегляд | Keyboard interactions загальні |  | Shift key має перемикати shift mode у controller. | adopted | WF-CANV-INPUT | REQ-CANV-INPUT-001 |  |
| FR-147 | Canvas і перегляд | Рендеринг canvas |  | Застосунок має регулярно оновлювати canvas frame при змінах. | adopted | WF-CANV-RENDER | REQ-CANV-RENDER-001 |  |
| FR-186 | Canvas і перегляд | Перемикання visibility/render modes |  | Застосунок має блокувати editing, коли figures hidden у non-segmentation mode. | adopted | WF-CANV-RENDER | REQ-CANV-RENDER-001 |  |
| FR-187 | Canvas і перегляд | Перемикання visibility/render modes |  | Застосунок має дозволяти segmentation editing навіть при hidden figures logic exception. | adopted | WF-CANV-RENDER | REQ-CANV-RENDER-001 |  |
| FR-188 | Canvas і перегляд | Рендеринг canvas |  | Застосунок має підтримувати opacity для objects overlay. | adopted | WF-CANV-RENDER | REQ-CANV-RENDER-001 |  |
| FR-189 | Canvas і перегляд | Рендеринг canvas |  | Застосунок має підтримувати opacity для fill color overlay. | adopted | WF-CANV-RENDER | REQ-CANV-RENDER-001 |  |
| FR-190 | Canvas і перегляд | Перемикання visibility/render modes |  | Застосунок має малювати crosshair для bbox mode. | adopted | WF-CANV-RENDER | REQ-CANV-RENDER-001 |  |
| FR-193 | Canvas і перегляд | Keyboard interactions загальні |  | Застосунок має обмежувати занадто швидке frame switching через min interval у keyboard handler. | adopted | WF-CANV-INPUT | REQ-CANV-INPUT-001 |  |
| FR-148 | Filtering workflow | Дані filtering project |  | У filtering mode застосунок має завантажувати video file video.mp4. | adopted | WF-FILT-DATA | REQ-FILT-DATA-001 |  |
| FR-149 | Filtering workflow | Дані filtering project |  | У filtering mode застосунок має завантажувати metadata meta.json. | adopted | WF-FILT-DATA | REQ-FILT-DATA-001 |  |
| FR-150 | Filtering workflow | Дані filtering project |  | У filtering mode застосунок має читати frames з video через OpenCV. | adopted | WF-FILT-DATA | REQ-FILT-DATA-001 |  |
| FR-153 | Filtering workflow | Дані filtering project |  | У filtering mode застосунок має декодувати image name з barcode внизу frame, якщо можливо. | adopted | WF-FILT-DATA | REQ-FILT-DATA-001 |  |
| FR-154 | Filtering workflow | Дані filtering project |  | Якщо image name не декодується, filtering item має ідентифікуватися за item id. | adopted | WF-FILT-DATA | REQ-FILT-DATA-001 |  |
| FR-155 | Filtering workflow | Навігація і selection |  | У filtering mode користувач може перемикатися між frames вперед і назад. | adopted | WF-FILT-JUMP | REQ-FILT-JUMP-001 |  |
| FR-156 | Filtering workflow | Навігація і selection |  | У filtering mode користувач може позначати поточний frame як selected/unselected. | adopted | WF-FILT-SELECT | REQ-FILT-SELECT-001 |  |
| FR-157 | Filtering workflow | Навігація і selection |  | У filtering mode selected frame має показуватися з зеленою рамкою. | adopted | WF-FILT-SELECT | REQ-FILT-SELECT-001 |  |
| FR-158 | Filtering workflow | Навігація і selection |  | У filtering mode користувач може перейти до наступного selected frame. | adopted | WF-FILT-JUMP | REQ-FILT-JUMP-001 |  |
| FR-159 | Filtering workflow | Навігація і selection |  | У filtering mode користувач може перейти до попереднього selected frame. | adopted | WF-FILT-JUMP | REQ-FILT-JUMP-001 |  |
| FR-160 | Filtering workflow | Delay/performance controls |  | У filtering mode користувач може змінювати delay між frames через keyboard. | adopted | WF-FILT-DELAY | REQ-FILT-DELAY-001 |  |
| FR-161 | Filtering workflow | Delay/performance controls |  | Filtering delay має підтримувати режими no delay, short, middle і long. | adopted | WF-FILT-DELAY | REQ-FILT-DELAY-001 |  |
| FR-162 | Filtering workflow | Delay/performance controls |  | У filtering mode користувач може перемикати degraded image preview. | adopted | WF-FILT-DELAY | REQ-FILT-DELAY-001 |  |
| FR-042 | Help і документація | Help/Hotkeys/HTML pages |  | Користувач може переглянути help page через Help > How to use this tool?. | adopted | WF-HELP-HOW | REQ-HELP-HOW-001 |  |
| FR-043 | Help і документація | Help/Hotkeys/HTML pages |  | Користувач може переглянути hotkeys page через Help > Hotkeys. | adopted | WF-HELP-HOTKEYS | REQ-HELP-HOTKEYS-001 |  |
| FR-044 | Help і документація | Help/Hotkeys/HTML pages |  | Help і hotkeys мають відкриватися як HTML windows. | adopted | WF-HELP-HOTKEYS | REQ-HELP-HOTKEYS-001 |  |
| FR-045 | Help і документація | Перегляд classes і review labels |  | Користувач може переглянути список classes через Help > Classes. | adopted | WF-LABL-HELP | REQ-LABL-HELP-001 |  |
| FR-046 | Help і документація | Перегляд classes і review labels |  | Для image labeling користувач може переглянути список review labels через Help > Review Labels. | adopted | WF-LABL-HELP | REQ-LABL-HELP-001 |  |
| FR-099 | Keypoints | Створення і редагування keypoints |  | У keypoints mode користувач може створювати keypoint groups на основі class attributes. | adopted | WF-LABL-KPOINT | REQ-LABL-KPOINT-001 |  |
| FR-100 | Keypoints | Створення і редагування keypoints |  | Keypoint group має створюватися через bbox-like placement із автоматичним розташуванням keypoints відносно box. | adopted | WF-LABL-KPOINT | REQ-LABL-KPOINT-001 |  |
| FR-101 | Keypoints | Створення і редагування keypoints |  | Keypoint group має підтримувати reflect по x/y залежно від напрямку створення. | adopted | WF-LABL-KPOINT | REQ-LABL-KPOINT-001 |  |
| FR-102 | Keypoints | Створення і редагування keypoints |  | Користувач може переміщати окремі keypoints. | adopted | WF-LABL-KPOINT | REQ-LABL-KPOINT-001 |  |
| FR-103 | Keypoints | Створення і редагування keypoints |  | Користувач може видаляти keypoints, а при критично малій кількості - весь group. | adopted | WF-LABL-KPOINT | REQ-LABL-KPOINT-001 |  |
| FR-104 | Keypoints | Створення і редагування keypoints |  | Keypoints мають малюватися з кольорами з label attributes. | adopted | WF-LABL-KPOINT | REQ-LABL-KPOINT-001 |  |
| FR-105 | Keypoints | Створення і редагування keypoints |  | Keypoint connections мають малюватися згідно з label attributes. | adopted | WF-LABL-KPOINT | REQ-LABL-KPOINT-001 |  |
| FR-106 | Keypoints | Створення і редагування keypoints |  | Користувач може показувати keypoint names. | adopted | WF-LABL-KPOINT | REQ-LABL-KPOINT-001 |  |
| FR-063 | Labeling workflow | Стадії і відбір images | 1 | У correction stage користувач має бачити тільки images, які мають review labels. | adopted | WF-LABL-SWITCH | REQ-LABL-SWITCH-001 |  |
| FR-064 | Labeling workflow | Стадії і відбір images | 1 | У review stage користувач має бачити тільки images, які require annotation. | adopted | WF-LABL-SWITCH | REQ-LABL-SWITCH-001 |  |
| FR-009 | Labeling workflow | Стадії і відбір images |  | Застосунок має підтримувати annotation modes: object detection, segmentation, keypoints, filtering і event validation. | adopted | WF-PROJ-OPEN | REQ-PROJ-OPEN-001 | global mode/stage support tracked here in first pass; EV is in Linux PySide scope as of 2026-04-24 |
| FR-010 | Labeling workflow | Стадії і відбір images |  | Застосунок має підтримувати annotation stages: annotate, review, correction, sent for review, sent for correction, done, filtering, event validation і unknown. | adopted | WF-PROJ-OPEN | REQ-PROJ-OPEN-001 | global mode/stage support tracked here in first pass; EV stages are in Linux PySide scope as of 2026-04-24 |
| FR-065 | Labeling workflow | Стадії і відбір images |  | У annotate stage користувач має бачити всі images project. | adopted | WF-LABL-SWITCH | REQ-LABL-SWITCH-001 |  |
| FR-076 | Labeling workflow | Робота з classes |  | Користувач може змінити label вибраного object. | adopted | WF-LABL-CLASS | REQ-LABL-CLASS-001 |  |
| FR-077 | Labeling workflow | Object lifecycle загальний |  | Користувач може копіювати selected object або всі objects. | adopted | WF-LABL-HISTORY | REQ-LABL-HISTORY-001 |  |
| FR-078 | Labeling workflow | Object lifecycle загальний |  | Користувач може вставляти скопійовані objects. | adopted | WF-LABL-HISTORY | REQ-LABL-HISTORY-001 |  |
| FR-079 | Labeling workflow | Object lifecycle загальний |  | Користувач може скопіювати annotations з попереднього image. | adopted | WF-LABL-HISTORY | REQ-LABL-HISTORY-001 |  |
| FR-080 | Labeling workflow | Object lifecycle загальний |  | Користувач може виконувати undo для object changes. | adopted | WF-LABL-HISTORY | REQ-LABL-HISTORY-001 |  |
| FR-081 | Labeling workflow | Object lifecycle загальний |  | Користувач може виконувати redo для object changes. | adopted | WF-LABL-HISTORY | REQ-LABL-HISTORY-001 |  |
| FR-089 | Labeling workflow | Trash/review behavior |  | Користувач може позначити image як trash у non-review stages. | adopted | WF-LABL-TRASH | REQ-LABL-TRASH-001 |  |
| FR-090 | Labeling workflow | Trash/review behavior |  | У review stage користувач не може змінювати trash tag. | adopted | WF-LABL-TRASH | REQ-LABL-TRASH-001 |  |
| FR-091 | Labeling workflow | Trash/review behavior |  | У review stage користувач може створювати review labels. | adopted | WF-LABL-TRASH | REQ-LABL-TRASH-001 |  |
| FR-092 | Labeling workflow | Trash/review behavior |  | Review label має створюватися одним кліком. | adopted | WF-LABL-TRASH | REQ-LABL-TRASH-001 |  |
| FR-093 | Labeling workflow | Trash/review behavior |  | Review label має показувати callout із текстом label і лінією до точки. | adopted | WF-LABL-TRASH | REQ-LABL-TRASH-001 |  |
| FR-139 | Labeling workflow | Робота з classes |  | Користувач може вибирати class numeric hotkeys. | adopted | WF-LABL-CLASS | REQ-LABL-CLASS-001 |  |
| FR-140 | Labeling workflow | Робота з classes |  | Користувач може утримувати a, щоб відкрити radial class selector. | adopted | WF-LABL-CLASS | REQ-LABL-CLASS-001 |  |
| FR-141 | Labeling workflow | Робота з classes |  | Після відпускання a має вибиратися class відповідно до сектору radial selector. | adopted | WF-LABL-CLASS | REQ-LABL-CLASS-001 |  |
| FR-142 | Labeling workflow | Робота з classes |  | Radial class selector має показувати labels, colors і highlighted selected sector. | adopted | WF-LABL-CLASS | REQ-LABL-CLASS-001 |  |
| FR-070 | Object detection | Створення і редагування bbox |  | У object detection mode користувач може створювати bounding boxes на зображенні. | adopted | WF-LABL-BBOX | REQ-LABL-BBOX-001 |  |
| FR-071 | Object detection | Створення і редагування bbox |  | Користувач може створити bbox двома кліками або drag-like workflow через start/end points. | adopted | WF-LABL-BBOX | REQ-LABL-BBOX-001 |  |
| FR-072 | Object detection | Створення і редагування bbox |  | Користувач може вибирати bbox під курсором. | adopted | WF-LABL-BBOX | REQ-LABL-BBOX-001 |  |
| FR-073 | Object detection | Створення і редагування bbox |  | Користувач може переміщати bbox corner points. | adopted | WF-LABL-BBOX | REQ-LABL-BBOX-001 |  |
| FR-074 | Object detection | Створення і редагування bbox |  | Користувач може видалити вибраний bbox або його point. | adopted | WF-LABL-BBOX | REQ-LABL-BBOX-001 |  |
| FR-075 | Object detection | Створення і редагування bbox |  | Користувач може видалити всі objects на image. | adopted | WF-LABL-BBOX | REQ-LABL-BBOX-001 |  |
| FR-082 | Object detection | Створення і редагування bbox |  | Застосунок має малювати bbox border з configurable line width. | adopted | WF-LABL-BBOX | REQ-LABL-BBOX-001 |  |
| FR-083 | Object detection | Створення і редагування bbox |  | Застосунок має показувати active bbox handle з configurable size. | adopted | WF-LABL-BBOX | REQ-LABL-BBOX-001 |  |
| FR-084 | Object detection | Створення і редагування bbox |  | Застосунок має підтримувати configurable cursor proximity threshold для вибору points. | adopted | WF-LABL-BBOX | REQ-LABL-BBOX-001 |  |
| FR-194 | Object detection | Створення і редагування bbox |  | Застосунок має підтримувати object selection priority за меншою surface area. | adopted | WF-LABL-BBOX | REQ-LABL-BBOX-001 |  |
| FR-107 | Segmentation | Створення і редагування masks |  | У segmentation mode користувач може створювати polygon selection для редагування mask. | adopted | WF-LABL-MASK | REQ-LABL-MASK-001 |  |
| FR-108 | Segmentation | Створення і редагування masks |  | У segmentation mode normal mode має додавати область до mask. | adopted | WF-LABL-MASK | REQ-LABL-MASK-001 |  |
| FR-109 | Segmentation | Створення і редагування masks |  | У segmentation mode shift mode має видаляти область з mask. | adopted | WF-LABL-MASK | REQ-LABL-MASK-001 |  |
| FR-110 | Segmentation | Створення і редагування masks |  | Користувач може завершити polygon, клікнувши біля його стартової точки. | adopted | WF-LABL-MASK | REQ-LABL-MASK-001 |  |
| FR-111 | Segmentation | Створення і редагування masks |  | Користувач може завершити polygon через space. | adopted | WF-LABL-MASK | REQ-LABL-MASK-001 |  |
| FR-112 | Segmentation | Створення і редагування masks |  | Користувач може скасувати polygon creation через escape. | adopted | WF-LABL-MASK | REQ-LABL-MASK-001 |  |
| FR-113 | Segmentation | Створення і редагування masks |  | Користувач може видалити mask активного class. | adopted | WF-LABL-MASK | REQ-LABL-MASK-001 |  |
| FR-115 | Segmentation | Створення і редагування masks |  | Segmentation masks мають декодуватися з RLE для редагування і показу. | adopted | WF-LABL-MASK | REQ-LABL-MASK-001 |  |
| FR-116 | Segmentation | Створення і редагування masks |  | Empty mask має створюватися як RLE для image dimensions. | adopted | WF-LABL-MASK | REQ-LABL-MASK-001 |  |
| FR-117 | Segmentation | Створення і редагування masks |  | На canvas masks мають малюватися поверх image з opacity. | adopted | WF-LABL-MASK | REQ-LABL-MASK-001 |  |
| FR-144 | UI shell | Status bars |  | Status bar для labeling має показувати mode, stage, active class, trash state, hidden state, item id, speed, progress і duration. | adopted | WF-PROJ-GOTO | REQ-PROJ-GOTO-001 |  |
| FR-145 | UI shell | Status bars |  | Status bar має адаптувати font size до ширини window. | adopted | WF-LABL-SWITCH | REQ-LABL-SWITCH-001 |  |
| FR-146 | UI shell | Status bars |  | Застосунок має регулярно оновлювати status bar під час роботи. | adopted | WF-LABL-SWITCH | REQ-LABL-SWITCH-001 |  |
| FR-163 | UI shell | Status bars |  | Filtering status bar має показувати mode, delay, selected state, item id, speed, selected ratio, position progress і duration. | adopted | WF-PROJ-GOTO | REQ-PROJ-GOTO-001 |  |
| FR-174 | UI shell | Меню, діалоги, повідомлення |  | Застосунок має показувати copyable error window для MessageBoxException. | adopted | WF-LABL-SWITCH | REQ-LABL-SWITCH-001 |  |
| FR-175 | UI shell | Меню, діалоги, повідомлення |  | Error window має містити scrollable text area і Close button. | adopted | WF-LABL-SWITCH | REQ-LABL-SWITCH-001 |  |
| FR-052 | Дані і backend | Імпорт annotation data | 1 | Якщо кількість images і annotations не збігається, застосунок має показати blocking error. | adopted | WF-PROJ-DOWNLOAD | REQ-PROJ-DOWNLOAD-001 |  |
| FR-062 | Дані і backend | Імпорт annotation data | 1 | Якщо review.json не містить жодного image з review labels, усі images мають бути доступні для correction/review workflow. | adopted | WF-PROJ-DOWNLOAD | REQ-PROJ-DOWNLOAD-001 |  |
| FR-164 | Дані і backend | Експорт annotation data | 1 | Filtering selected frames мають експортуватися у selected_frames.json. | adopted | WF-PROJ-COMPLETE | REQ-PROJ-COMPLETE-001 |  |
| FR-167 | Дані і backend | Overwrite annotations | 1 | Для filtering project overwrite annotations має бути недоступний і показувати повідомлення not implemented. | adopted | WF-FILT-DATA | REQ-FILT-DATA-001 | unsupported overwrite path in filtering mode is tracked here in the first pass |
| FR-171 | Дані і backend | File download/upload | 1 | Якщо optional file download повертає 404 і ignore_404=True, застосунок має продовжити роботу. | adopted | WF-PROJ-DOWNLOAD | REQ-PROJ-DOWNLOAD-001 |  |
| FR-007 | Дані і backend | Progress windows для transfer/unzip |  | Застосунок має показувати loading/progress windows під час отримання списку projects, download, unzip, overwrite і completion. | adopted | WF-LABL-OVERWRITE | REQ-LABL-OVERWRITE-001 |  |
| FR-047 | Дані і backend | Імпорт annotation data |  | Застосунок має завантажувати project metadata meta.json. | adopted | WF-PROJ-DOWNLOAD | REQ-PROJ-DOWNLOAD-001 |  |
| FR-048 | Дані і backend | Імпорт annotation data |  | Застосунок має завантажувати image annotation file figures.json. | adopted | WF-PROJ-DOWNLOAD | REQ-PROJ-DOWNLOAD-001 |  |
| FR-049 | Дані і backend | Імпорт annotation data |  | Застосунок має завантажувати review annotation file review.json, якщо він існує. | adopted | WF-PROJ-DOWNLOAD | REQ-PROJ-DOWNLOAD-001 |  |
| FR-050 | Дані і backend | Імпорт annotation data |  | Застосунок має завантажувати image archive archive.zip і розпаковувати його в локальну папку images. | adopted | WF-PROJ-DOWNLOAD | REQ-PROJ-DOWNLOAD-001 |  |
| FR-051 | Дані і backend | Імпорт annotation data |  | Застосунок має перевіряти, що кількість images відповідає кількості annotations. | adopted | WF-PROJ-DOWNLOAD | REQ-PROJ-DOWNLOAD-001 |  |
| FR-053 | Дані і backend | Імпорт annotation data |  | Застосунок має імпортувати labels з metadata у локальну database. | adopted | WF-PROJ-DOWNLOAD | REQ-PROJ-DOWNLOAD-001 |  |
| FR-054 | Дані і backend | Імпорт annotation data |  | Застосунок має імпортувати review labels з metadata у локальну database. | adopted | WF-PROJ-DOWNLOAD | REQ-PROJ-DOWNLOAD-001 |  |
| FR-055 | Дані і backend | Імпорт annotation data |  | Застосунок має автоматично додавати label blur для bbox або mask workflow. | adopted | WF-PROJ-DOWNLOAD | REQ-PROJ-DOWNLOAD-001 |  |
| FR-056 | Дані і backend | Імпорт annotation data |  | Застосунок має імпортувати bboxes з figures.json. | adopted | WF-PROJ-DOWNLOAD | REQ-PROJ-DOWNLOAD-001 |  |
| FR-057 | Дані і backend | Імпорт annotation data |  | Застосунок має імпортувати keypoint groups з figures.json. | adopted | WF-PROJ-DOWNLOAD | REQ-PROJ-DOWNLOAD-001 |  |
| FR-058 | Дані і backend | Імпорт annotation data |  | Застосунок має імпортувати masks з figures.json. | adopted | WF-PROJ-DOWNLOAD | REQ-PROJ-DOWNLOAD-001 |  |
| FR-059 | Дані і backend | Імпорт annotation data |  | Застосунок має імпортувати trash tag для images з figures.json. | adopted | WF-PROJ-DOWNLOAD | REQ-PROJ-DOWNLOAD-001 |  |
| FR-060 | Дані і backend | Імпорт annotation data |  | Застосунок має імпортувати image dimensions з annotations або actual image files. | adopted | WF-PROJ-DOWNLOAD | REQ-PROJ-DOWNLOAD-001 |  |
| FR-061 | Дані і backend | Імпорт annotation data |  | Застосунок має імпортувати review labels з review.json. | adopted | WF-PROJ-DOWNLOAD | REQ-PROJ-DOWNLOAD-001 |  |
| FR-066 | Дані і backend | Overwrite annotations |  | Користувач може примусово завантажити і перезаписати annotations через Download and overwrite annotations. | adopted | WF-LABL-OVERWRITE | REQ-LABL-OVERWRITE-001 |  |
| FR-068 | Дані і backend | Overwrite annotations |  | Перед overwrite annotations застосунок має питати підтвердження користувача. | adopted | WF-LABL-OVERWRITE | REQ-LABL-OVERWRITE-001 |  |
| FR-069 | Дані і backend | Overwrite annotations |  | Після overwrite annotations застосунок має перезавантажити поточний item і оновити canvas. | adopted | WF-LABL-OVERWRITE | REQ-LABL-OVERWRITE-001 |  |
| FR-094 | Дані і backend | Експорт annotation data |  | Review labels мають експортуватися в review.json. | adopted | WF-PROJ-DOWNLOAD | REQ-PROJ-DOWNLOAD-001 |  |
| FR-095 | Дані і backend | Експорт annotation data |  | Annotation figures мають експортуватися в figures.json. | adopted | WF-PROJ-DOWNLOAD | REQ-PROJ-DOWNLOAD-001 |  |
| FR-114 | Дані і backend | Експорт annotation data |  | Segmentation masks мають зберігатися у RLE format. | adopted | WF-PROJ-DOWNLOAD | REQ-PROJ-DOWNLOAD-001 |  |
| FR-165 | Дані і backend | Експорт annotation data |  | selected_frames.json має містити selected image names або item ids. | adopted | WF-PROJ-COMPLETE | REQ-PROJ-COMPLETE-001 |  |
| FR-168 | Дані і backend | File download/upload |  | File download має виконуватись потоково з progress percent, completed size, speed і remaining time. | adopted | WF-PROJ-DOWNLOAD | REQ-PROJ-DOWNLOAD-001 |  |
| FR-169 | Дані і backend | File download/upload |  | File upload має виконуватись на backend file service з authorization token. | adopted | WF-PROJ-COMPLETE | REQ-PROJ-COMPLETE-001 |  |
| FR-172 | Дані і backend | Progress windows для transfer/unzip |  | Unzip має виконуватись з progress percent, processed size, speed і remaining time. | adopted | WF-PROJ-DOWNLOAD | REQ-PROJ-DOWNLOAD-001 |  |
| FR-173 | Дані і backend | Progress windows для transfer/unzip |  | Користувач може закрити progress window, щоб сигналізувати termination processing. | adopted | WF-PROJ-DOWNLOAD | REQ-PROJ-DOWNLOAD-001 |  |
| FR-151 | Дані моделі | Images/items ordering |  | У filtering mode кожен video frame має відповідати item для перегляду. | adopted | WF-LABL-SWITCH | REQ-LABL-SWITCH-001 |  |
| FR-152 | Дані моделі | Images/items ordering |  | У filtering mode застосунок має визначати кількість items за frame count video. | adopted | WF-LABL-SWITCH | REQ-LABL-SWITCH-001 |  |
| FR-195 | Дані моделі | Images/items ordering |  | Застосунок має сортувати images за name. | adopted | WF-LABL-SWITCH | REQ-LABL-SWITCH-001 |  |
| FR-196 | Дані моделі | Labels і ordering |  | Застосунок має сортувати labels за hotkey. | adopted | WF-LABL-CLASS | REQ-LABL-CLASS-001 |  |
| FR-197 | Дані моделі | Labels і ordering |  | Застосунок має показувати class list з label name, type, color і hotkey. | adopted | WF-LABL-CLASS | REQ-LABL-CLASS-001 |  |
| FR-198 | Дані моделі | Labels і ordering |  | Class list для keypoints має додатково показувати keypoint names і colors з label attributes. | adopted | WF-LABL-CLASS | REQ-LABL-CLASS-001 |  |
| FR-032 | Інтеграція backend | API доступність і fallback | 1 | Якщо backend недоступний, completion має блокуватись із повідомленням про помилку. | adopted | WF-PROJ-OPEN | REQ-PROJ-OPEN-001 |  |
| FR-170 | Інтеграція backend | API доступність і fallback | 1 | Якщо download повертає non-200 response, застосунок має показувати error message. | adopted | WF-PROJ-DOWNLOAD | REQ-PROJ-DOWNLOAD-001 |  |
| FR-180 | Інтеграція backend | API доступність і fallback | 1 | Застосунок має перевіряти доступність backend URL перед completion і overwrite. | adopted | WF-PROJ-OPEN | REQ-PROJ-OPEN-001 |  |
| FR-067 | Інтеграція backend | API доступність і fallback |  | Перед overwrite annotations застосунок має перевіряти доступність backend. | adopted | WF-PROJ-OPEN | REQ-PROJ-OPEN-001 |  |
| FR-176 | Інтеграція backend | API доступність і fallback |  | Backend API має отримувати список projects з user token. | adopted | WF-PROJ-OPEN | REQ-PROJ-OPEN-001 |  |
| FR-177 | Інтеграція backend | API доступність і fallback |  | Backend API має фільтрувати projects assigned to current user, якщо це потрібно. | adopted | WF-PROJ-OPEN | REQ-PROJ-OPEN-001 |  |
| FR-178 | Інтеграція backend | API доступність і fallback |  | Backend API має отримувати актуальні project stage і mode за uid. | adopted | WF-PROJ-OPEN | REQ-PROJ-OPEN-001 |  |
| FR-179 | Інтеграція backend | API доступність і fallback |  | Backend API має завершувати task із передачею duration hours. | adopted | WF-PROJ-OPEN | REQ-PROJ-OPEN-001 |  |
| FR-024 | Конфігурація | Налаштування застосунку | 1 | Якщо required settings порожні, застосунок має показати settings manager перед запуском основного workflow. | adopted | WF-PROJ-SETTINGS | REQ-PROJ-SETTINGS-001 |  |
| FR-020 | Конфігурація | Налаштування застосунку |  | Користувач може відкрити settings через меню Project > Settings. | adopted | WF-PROJ-SETTINGS | REQ-PROJ-SETTINGS-001 |  |
| FR-021 | Конфігурація | Налаштування застосунку |  | Застосунок має зберігати settings у settings.json. | adopted | WF-PROJ-SETTINGS | REQ-PROJ-SETTINGS-001 |  |
| FR-022 | Конфігурація | Налаштування застосунку |  | Settings мають містити token, api url, file url і data directory. | adopted | WF-PROJ-SETTINGS | REQ-PROJ-SETTINGS-001 |  |
| FR-023 | Конфігурація | Налаштування застосунку |  | Settings мають містити UI-параметри: bbox line width, cursor proximity threshold, objects opacity, fill opacity, bbox handler size і keypoint handler size. | adopted | WF-PROJ-SETTINGS | REQ-PROJ-SETTINGS-001 |  |
| FR-025 | Конфігурація | Налаштування застосунку |  | Якщо data_dir не можна створити, застосунок має показати error window і очистити некоректне значення. | adopted | WF-PROJ-SETTINGS | REQ-PROJ-SETTINGS-001 |  |
| FR-026 | Платформа і запуск | Оновлення застосунку | 1 | Користувач може оновити застосунок через Project > Update tool, що виконує git pull. | adopted | WF-PROJ-UPDATE | REQ-PROJ-UPDATE-001 |  |
| FR-001 | Платформа і запуск | Запуск застосунку |  | Користувач може запускати desktop-застосунок для annotation tool у повноекранному вікні з іконкою, меню та робочою областю. | adopted | WF-PROJ-BOOTSTRAP | REQ-PROJ-BOOTSTRAP-001 |  |
| FR-002 | Платформа і запуск | Інсталяція Linux/macOS |  | Застосунок має підтримувати Linux-інсталяцію через shell script зі створенням virtual environment, встановленням dependencies, font і desktop shortcut. | superseded |  |  | superseded by ADR `0002` because the row sits under a combined Linux/macOS installer scope even though its text is Linux-only, and the first release path now narrows PySide support to Linux while macOS stays on Tk |
| FR-027 | Платформа і запуск | Оновлення застосунку |  | Після оновлення застосунок має показати результат git pull і повідомити, що потрібно перезапустити tool. | adopted | WF-PROJ-UPDATE | REQ-PROJ-UPDATE-001 |  |
| FR-182 | Платформа і запуск | Запуск застосунку |  | Застосунок має показувати project id у window title після відкриття project. | adopted | WF-PROJ-BOOTSTRAP | REQ-PROJ-BOOTSTRAP-001 |  |
| FR-005 | Проєкти | Отримання і вибір project | 1 | Якщо backend недоступний, користувач може відкривати вже завантажені локальні projects. | adopted | WF-PROJ-OPEN | REQ-PROJ-OPEN-001 | local-open fallback when backend is unavailable |
| FR-006 | Проєкти | Отримання і вибір project | 1 | Користувач може завантажити project з backend через меню Project > Download. | adopted | WF-PROJ-DOWNLOAD | REQ-PROJ-DOWNLOAD-001 |  |
| FR-019 | Проєкти | Видалення і очищення project | 1 | Застосунок має автоматично видаляти локальні projects, які більше не є активними на backend. | adopted | WF-PROJ-REMOVE | REQ-PROJ-REMOVE-001 |  |
| FR-033 | Проєкти | Завершення project | 1 | Під час completion застосунок має upload statistics file, якщо він існує. | adopted | WF-PROJ-COMPLETE | REQ-PROJ-COMPLETE-001 |  |
| FR-034 | Проєкти | Завершення project | 1 | Під час completion застосунок має upload annotation results відповідно до типу project. | adopted | WF-PROJ-COMPLETE | REQ-PROJ-COMPLETE-001 |  |
| FR-035 | Проєкти | Завершення project | 1 | Під час completion застосунок має надіслати duration hours на backend. | adopted | WF-PROJ-COMPLETE | REQ-PROJ-COMPLETE-001 |  |
| FR-036 | Проєкти | Завершення project | 1 | Після completion застосунок має reset counters, оновити локальний stage і прибрати project files за правилами конкретного mode/stage. | adopted | WF-PROJ-COMPLETE | REQ-PROJ-COMPLETE-001 |  |
| FR-096 | Проєкти | Завершення project | 1 | У annotate або correction stage completion має переводити project у SENT_FOR_REVIEW. | adopted | WF-PROJ-COMPLETE | REQ-PROJ-COMPLETE-001 |  |
| FR-097 | Проєкти | Завершення project | 1 | У review stage completion має переводити project у SENT_FOR_CORRECTION. | adopted | WF-PROJ-COMPLETE | REQ-PROJ-COMPLETE-001 |  |
| FR-098 | Проєкти | Завершення project | 1 | Якщо review завершено без review labels, local project має бути видалений після completion. | adopted | WF-PROJ-COMPLETE | REQ-PROJ-COMPLETE-001 |  |
| FR-166 | Проєкти | Завершення project | 1 | Під час completion filtering project має upload selected_frames.json. | adopted | WF-PROJ-COMPLETE | REQ-PROJ-COMPLETE-001 |  |
| FR-183 | Проєкти | Навігація по project | 1 | Після закриття window застосунок має зберігати поточний item і annotation changes. | adopted | WF-PROJ-RUNTIME | REQ-PROJ-RUNTIME-001 |  |
| FR-184 | Проєкти | Навігація по project | 1 | Перед перемиканням item застосунок має зберігати зміни поточного item. | adopted | WF-PROJ-RUNTIME | REQ-PROJ-RUNTIME-001 |  |
| FR-004 | Проєкти | Отримання і вибір project |  | Користувач може відкрити список доступних annotation projects через меню Project > Open. | adopted | WF-PROJ-OPEN | REQ-PROJ-OPEN-001 |  |
| FR-008 | Проєкти | Отримання і вибір project |  | Користувач може вибрати project зі списку через GUI selector. | adopted | WF-PROJ-OPEN | REQ-PROJ-OPEN-001 |  |
| FR-011 | Проєкти | Локальне зберігання project |  | Застосунок має створювати локальну папку project data за project id. | adopted | WF-PROJ-DOWNLOAD | REQ-PROJ-DOWNLOAD-001 |  |
| FR-012 | Проєкти | Локальне зберігання project |  | Застосунок має зберігати локальний state project у state.json. | adopted | WF-PROJ-DOWNLOAD | REQ-PROJ-DOWNLOAD-001 |  |
| FR-013 | Проєкти | Локальне зберігання project |  | Застосунок має використовувати локальну SQLite database для project state, labels, images, figures, masks, keypoints, review labels і filtering selections. | adopted | WF-PROJ-RUNTIME | REQ-PROJ-RUNTIME-001 |  |
| FR-014 | Проєкти | Локальне зберігання project |  | Застосунок має автоматично конфігурувати SQLite database перед роботою з project. | adopted | WF-PROJ-RUNTIME | REQ-PROJ-RUNTIME-001 |  |
| FR-015 | Проєкти | Локальне зберігання project |  | Застосунок має підтримувати WAL journal mode і shared SQLite access для роботи з GUI. | adopted | WF-PROJ-RUNTIME | REQ-PROJ-RUNTIME-001 |  |
| FR-016 | Проєкти | Локальне зберігання project |  | Застосунок має валідувати локальний project через наявність state.json, коректний JSON і db.sqlite. | adopted | WF-PROJ-DOWNLOAD | REQ-PROJ-DOWNLOAD-001 |  |
| FR-017 | Проєкти | Видалення і очищення project |  | Користувач може видалити локальний project через меню Project > Remove project by ID. | adopted | WF-PROJ-REMOVE | REQ-PROJ-REMOVE-001 |  |
| FR-018 | Проєкти | Видалення і очищення project |  | Видалення локального project має прибирати його файли з компʼютера, але не видаляти project з backend. | adopted | WF-PROJ-REMOVE | REQ-PROJ-REMOVE-001 |  |
| FR-028 | Проєкти | Навігація по project |  | Користувач може перейти до конкретного item id через меню Project > Go to ID. | adopted | WF-PROJ-GOTO | REQ-PROJ-GOTO-001 |  |
| FR-029 | Проєкти | Завершення project |  | Користувач може завершити project через меню Project > Complete the project. | adopted | WF-PROJ-COMPLETE | REQ-PROJ-COMPLETE-001 |  |
| FR-030 | Проєкти | Завершення project |  | Перед completion застосунок має запитувати підтвердження користувача. | adopted | WF-PROJ-COMPLETE | REQ-PROJ-COMPLETE-001 |  |
| FR-031 | Проєкти | Завершення project |  | Перед completion застосунок має виконувати validation через check_before_completion. | adopted | WF-PROJ-COMPLETE | REQ-PROJ-COMPLETE-001 |  |
| FR-181 | Проєкти | Видалення і очищення project |  | Застосунок має підтримувати local fallback для broken projects при видаленні. | adopted | WF-PROJ-REMOVE | REQ-PROJ-REMOVE-001 |  |
| FR-185 | Проєкти | Навігація по project |  | Після перемикання item застосунок має зберігати item id і processed ids. | adopted | WF-PROJ-RUNTIME | REQ-PROJ-RUNTIME-001 |  |
| FR-039 | Стан і persistence | Збереження runtime state | 1 | Застосунок має зберігати поточний item id між сесіями. | adopted | WF-PROJ-RUNTIME | REQ-PROJ-RUNTIME-001 |  |
| FR-040 | Стан і persistence | Збереження runtime state | 1 | Застосунок має зберігати duration hours між сесіями. | adopted | WF-PROJ-RUNTIME | REQ-PROJ-RUNTIME-001 |  |
| FR-037 | Стан і persistence | Збереження runtime state |  | Застосунок має вести duration tracking annotation часу з обмеженням одного action interval до 5 хвилин. | adopted | WF-PROJ-RUNTIME | REQ-PROJ-RUNTIME-001 |  |
| FR-038 | Стан і persistence | Збереження runtime state |  | Застосунок має писати statistics log із stage, datetime і action message. | adopted | WF-PROJ-RUNTIME | REQ-PROJ-RUNTIME-001 |  |
| FR-041 | Стан і persistence | Збереження runtime state |  | Застосунок має зберігати processed item ids між сесіями. | adopted | WF-PROJ-RUNTIME | REQ-PROJ-RUNTIME-001 |  |
| FR-191 | Стан і persistence | Лічильники і статистика |  | Користувач може бачити progress position як відсоток і item index з total count. | adopted | WF-PROJ-RUNTIME | REQ-PROJ-RUNTIME-001 |  |
| FR-192 | Стан і persistence | Лічильники і статистика |  | Користувач може бачити annotation speed у items/images per hour. | adopted | WF-PROJ-RUNTIME | REQ-PROJ-RUNTIME-001 |  |
