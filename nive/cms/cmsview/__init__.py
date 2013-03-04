
from nive.definitions import ModuleConf

configuration = ModuleConf(
    id="cms-view-module",
    name="Meta package to load cms editor components",
    modules=(
        "nive.cms.cmsview.cmsroot", 
        "nive.cms.cmsview.view", 
        "nive.components.reform.reformed"
    ),
)