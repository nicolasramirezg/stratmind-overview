import uuid
from typing import Optional, List, Dict, Set
from dataclasses import dataclass, field, asdict

class Status:
    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    DONE = "done"
    VALID = {PENDING, IN_PROGRESS, DONE}

@dataclass
class Task:
    title: str
    description: str
    expected_output: str
    area: Optional[str] = None
    parent: Optional['Task'] = None
    assigned_agent: Optional[str] = None
    status: str = Status.PENDING
    responsibilities: Optional[List[str]] = field(default_factory=list)
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()), init=False)
    dependencies: Set['Task'] = field(default_factory=set, repr=False)
    subtasks: List['Task'] = field(default_factory=list, repr=False)
    intro: Optional[str] = None
    execution_type: str = "llm"
    prompt: Optional[Dict[str, str]] = None   # <-- Add this line
    result: Optional[str] = None              # <-- Add this line
    manager: Optional['TaskManager'] = None

    def __post_init__(self):
        if self.status not in Status.VALID:
            raise ValueError(f"Invalid status: {self.status}")

    def __hash__(self):
        return hash(self.task_id)

    def __eq__(self, other):
        if not isinstance(other, Task):
            return False
        return self.task_id == other.task_id

    def add_subtask(self, subtask: 'Task') -> None:
        """
        Añade subtask como subtarea de esta tarea.
        Ajusta la referencia al padre en subtask.
        """
        subtask.parent = self
        self.subtasks.append(subtask)

    def add_dependency(self, dep: 'Task') -> None:
        """
        Añade una dependencia. Depende de que 'dep' se complete antes.
        Detecta ciclos y lanza excepción si hay dependencia circular.
        """
        if self.depends_on(dep):
            raise ValueError("Circular dependency detected")
        self.dependencies.add(dep)

    def depends_on(self, other: 'Task', visited: Optional[Set['Task']] = None) -> bool:
        """
        Revisa recursivamente si esta tarea depende de 'other'.
        """
        if visited is None:
            visited = set()
        if other in self.dependencies:
            return True
        visited.add(self)
        for d in self.dependencies:
            if d not in visited and d.depends_on(other, visited):
                return True
        return False

    def to_dict(self) -> Dict:
        """
        Serializes the task including dependencies, subtasks, and prompt/result.
        """
        data = {
            **{k: v for k, v in asdict(self).items() if k not in ('dependencies', 'subtasks', 'parent')},
            'area': self.area,
            'responsibilities': self.responsibilities,
            'dependencies': [d.task_id for d in self.dependencies],
            'subtasks': [s.to_dict() for s in self.subtasks],
            'parent_task_id': self.parent.task_id if self.parent else None,
            'prompt': self.prompt,    # <-- Add this line
            'result': self.result     # <-- Add this line
        }
        return data

class TaskManager:
    def __init__(self):
        self.tasks = {}
        self.root_task_id = None  # <-- Añade este atributo

    def create_task(
        self,
        title: str,
        description: str,
        expected_output: str,
        area: Optional[str] = None,
        parent_id: Optional[str] = None,
        assigned_agent: Optional[str] = None,
        status: str = Status.PENDING,
        responsibilities: Optional[List[str]] = None,
        execution_type: str = "llm"  # <-- Añadido aquí
    ) -> Task:
        """
        Crea una tarea y la registra en el manager.
        Si parent_id existe, la añade como subtarea.
        """
        task = Task(
            title=title,
            description=description,
            expected_output=expected_output,
            area=area,
            assigned_agent=assigned_agent,
            status=status,
            responsibilities=responsibilities or [],
            execution_type=execution_type,
            manager=self  # <-- Añadido aquí
        )
        self.tasks[task.task_id] = task
        # Si no tiene padre, es la raíz
        if parent_id is None:
            self.root_task_id = task.task_id
        if parent_id:
            parent = self.tasks.get(parent_id)
            if parent:
                parent.add_subtask(task)
        return task

    def add_dependency(self, task_id: str, dep_id: str) -> None:
        """
        Añade una dependencia entre dos tareas registradas.
        """
        t, d = self.tasks[task_id], self.tasks[dep_id]
        t.add_dependency(d)

    def get_execution_order(self) -> List[Task]:
        """
        Retorna una lista topológica de tareas según dependencias.
        Lanza excepción si ciclo.
        """
        visited = {}
        order: List[Task] = []

        def visit(t: Task):
            if visited.get(t.task_id) == 'temp':
                raise ValueError('Circular dependency detected during ordering')
            if visited.get(t.task_id) is None:
                visited[t.task_id] = 'temp'
                for dep in t.dependencies:
                    visit(dep)
                visited[t.task_id] = 'perm'
                order.append(t)

        for task in self.tasks.values():
            if visited.get(task.task_id) is None:
                visit(task)

        return order

    def to_dict(self) -> Dict[str, Dict]:
        """
        Serializa todas las tareas a diccionario.
        """
        return {tid: t.to_dict() for tid, t in self.tasks.items()}

def create_and_link_subtasks(subtasks, area, area_task, task_manager):
    """
    Crea objetos Task para cada subtask y asigna dependencias entre ellas usando títulos normalizados.
    Devuelve un diccionario {titulo_normalizado: Task}.
    """
    subtask_objs = {}
    for subtask in subtasks:
        t = task_manager.create_task(
            title=subtask["title"],
            description=subtask["description"],
            expected_output=subtask["expected_output"],
            area=area,
            parent_id=area_task.task_id,
            execution_type=subtask.get("execution_type", "llm")  # <-- Añadido aquí
        )
        subtask_objs[subtask["title"].strip().lower()] = t

    for subtask in subtasks:
        dependencies = subtask.get("dependencies", [])
        for dep_title in dependencies:
            dep_task = subtask_objs.get(dep_title.strip().lower())
            if dep_task:
                subtask_objs[subtask["title"].strip().lower()].add_dependency(dep_task)
    return subtask_objs
