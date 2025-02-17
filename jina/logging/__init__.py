from pkg_resources import resource_filename

from .logger import JinaLogger

__all__ = ['default_logger', 'profile_logger']

default_logger = JinaLogger('JINA')  #: a logger at the global-level
profile_logger = JinaLogger(
    'PROFILE',
    log_config=resource_filename(
        'jina', '/'.join(('resources', 'logging.profile.yml'))
    ),
)
