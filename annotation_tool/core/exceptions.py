class AnnotationToolError(Exception):
    pass


class UserVisibleError(AnnotationToolError):
    pass


class SettingsError(UserVisibleError):
    pass


class ProjectError(UserVisibleError):
    pass


class BackendError(UserVisibleError):
    pass


class ValidationError(UserVisibleError):
    pass
