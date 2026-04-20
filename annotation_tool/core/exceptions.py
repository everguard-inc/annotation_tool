class AnnotationToolError(Exception):
    ...


class UserVisibleError(AnnotationToolError):
    ...


class SettingsError(AnnotationToolError):
    ...


class ProjectError(AnnotationToolError):
    ...


class BackendError(AnnotationToolError):
    ...


class ValidationError(AnnotationToolError):
    ...
