from annotation_tool.core.models import ProjectData


class ImportExportService:
    def import_labeling_project(self, project: ProjectData) -> None:
        ...

    def import_filtering_project(self, project: ProjectData) -> None:
        ...

    def export_figures(self) -> None:
        ...

    def export_review_labels(self) -> None:
        ...

    def export_selected_frames(self) -> None:
        ...
