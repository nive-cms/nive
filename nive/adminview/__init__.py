
from nive.definitions import ModuleConf

configuration = ModuleConf(
    id="cms-admin-module",
    name="Meta package to load cms admin ui components",
    modules=(
        "nive.adminview.view", 
        "nive.components.reform.reformed"
    ),
)