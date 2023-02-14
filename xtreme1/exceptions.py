class SDKException(Exception):
    code = None

    def __init__(self, message='', code=None):
        if code:
            self.code = code
        super().__init__(f'<{self.code}> {message}')


class UrlNotFoundException(SDKException):
    code = 404


class ParamException(SDKException):
    code = 'PARAM_ERROR'


class DatasetIdException(SDKException):
    code = 'DATASET_NOT_FOUND'


class DataIdException(SDKException):
    code = 'DATA_NOT_FOUND'


class NameDuplicatedException(SDKException):
    code = 'NAME_DUPLICATED'


class DataUnlockedException(SDKException):
    code = 'DATASET__DATA__DATA_HAS_BEEN_UNLOCKED'


class ConverterException(SDKException):
    code = 'NOT_SUPPORT'


class SourceException(SDKException):
    code = 'UNPARSEABLE'


class NoPermissionException(SDKException):
    code = 'NO_PERMISSION'


class NodeIdException(SDKException):
    code = 'NODE_NOT_FOUND'


EXCEPTIONS = {
    ParamException.code: ParamException,
    DatasetIdException.code: DatasetIdException,
    DataIdException.code: DataIdException,
    NameDuplicatedException.code: NameDuplicatedException,
    ConverterException.code: ConverterException,
    DataUnlockedException.code: DataUnlockedException
}
