class ForecasterException(Exception):
    pass


class ScenarioNotFoundException(ForecasterException):
    pass


class AssetNotFoundException(ForecasterException):
    pass


class BadAssetScheduleTimeIntervalException(ForecasterException):
    pass


class DuplicateScenarioNameException(ForecasterException):
    pass
