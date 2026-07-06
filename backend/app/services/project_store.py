from app.models.pipeline import ProjectState


class ProjectStore:
    def __init__(self) -> None:
        self._projects: dict[str, ProjectState] = {}

    def create(self, project: ProjectState) -> ProjectState:
        self._projects[project.id] = project
        return project

    def get(self, project_id: str) -> ProjectState | None:
        return self._projects.get(project_id)

    def save(self, project: ProjectState) -> ProjectState:
        self._projects[project.id] = project
        return project

    def list(self) -> list[ProjectState]:
        return list(self._projects.values())

    def clear(self) -> None:
        self._projects.clear()


project_store = ProjectStore()
