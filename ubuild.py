from uranium import current_build

current_build.config.set_defaults({
    "module": "event_tracking"
})

current_build.packages.install("orbital-core")
from orbital_core.build import bootstrap_build
bootstrap_build(current_build)

@build.task
def build_statics(build):
    build.executables.run(["npm", "install", "."])
    build.executables.run(["gulp", "build"])

build.tasks.append("main", "build_statics")

@build.task
def start_db(build):
    build.executables.run(["/bin/bash", "-c", (
        "docker run -p 27017:27017 --name tycho-db"
        " -d mongo"
    )])

@build.task
def stop_db(build):
    build.executables.run(["/bin/bash", "-c", "docker stop tycho-db"])
    build.executables.run(["/bin/bash", "-c", "docker rm tycho-db"])

build.tasks.prepend("test", "start_db")
build.tasks.append("test", "stop_db")

def prep_app(build):
    """ prep to be run as an app. """
    build.packages.install("gunicorn")
