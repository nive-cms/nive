
from nive.definitions import ModuleConf

configuration = ModuleConf(
    id="useradmin-module",
    name="Meta package for useradmin components",
    modules=(
        "nive.userdb.useradmin.adminroot",
        "nive.userdb.useradmin.view",
        "nive.components.reform.reformed"
    ),
)

