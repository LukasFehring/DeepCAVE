import datetime
import sys
import os
from typing import Callable, Any, TypeVar, cast
from functools import wraps
import webbrowser
from threading import Timer

name = "DeepCAVE"
package_name = "deepcave"
author = "René Sass and Marius Lindauer"
author_email = "sass@tnt.uni-hannover.de"
description = "An interactive framework to visualize and analyze your AutoML process in real-time."
url = "automl.org"
project_urls = {
    "Documentation": "https://automl.github.io/DeepCAVE/main",
    "Source Code": "https://github.com/automl/deepcave",
}
copyright = f"Copyright {datetime.date.today().strftime('%Y')}, René Sass and Marius Lindauer"
version = "1.0"

_exec_file = sys.argv[0]
_exec_files = ["server.py", "worker.py", "sphinx-build"]


if any(file in _exec_file for file in _exec_files):
    from deepcave.queue import Queue
    from deepcave.runs.handler import RunHandler
    from deepcave.runs.objective import Objective  # noqa
    from deepcave.runs.recorder import Recorder  # noqa
    from deepcave.server import get_app
    from deepcave.utils.cache import Cache
    from deepcave.utils.run_caches import RunCaches
    from deepcave.utils.notification import Notification
    from deepcave.utils.configs import parse_config

    # Get config
    config_name = None
    if "--config" in sys.argv:
        config_name = sys.argv[sys.argv.index("--config") + 1]
    config = parse_config(config_name)

    # Create app
    app = get_app(config)
    queue = Queue(config.REDIS_ADDRESS, config.REDIS_PORT)

    if "server.py" in _exec_file:
        # Meta cache
        c = Cache(
            filename=config.CACHE_DIR / "meta.json",
            defaults=config.META_DEFAULT,
            debug=config.DEBUG,
        )

        # Set working directory to current directory
        if c.get("working_dir") is None:
            c.set("working_dir", value=os.getcwd())

        # Run caches
        rc = RunCaches(config)

        # Run Handler
        run_handler = RunHandler(config, c, rc)

        # Notifications
        notification = Notification()

        if "server.py" in _exec_file:
            # Open the link in browser
            def open_browser() -> None:
                webbrowser.open_new(f"http://{config.DASH_ADDRESS}:{config.DASH_PORT}")

            Timer(1, open_browser).start()

    __all__ = [
        "version",
        "app",
        "queue",
        "c",
        "rc",
        "run_handler",
        "notification",
        "config",
        "Recorder",
        "Objective",
    ]
else:
    try:
        from deepcave.runs.objective import Objective  # noqa
        from deepcave.runs.recorder import Recorder  # noqa

        __all__ = ["version", "Recorder", "Objective"]
    except ModuleNotFoundError:
        __all__ = ["version"]


_api_mode = False if "app" in globals() else True


# This TypeVar is necessary to ensure that the decorator works with arbitrary signatures.
F = TypeVar("F", bound=Callable[..., Any])


def interactive(func: F) -> F:
    @wraps(func)
    def inner(*args: Any, **kwargs: Any) -> Any:
        if _api_mode:
            return

        return func(*args, **kwargs)

    return cast(F, inner)
