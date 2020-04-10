import os
import shutil
import subprocess
from uranium import current_build, task_requires

# current_build.packages.install("uranium-plus[vscode]")
current_build.packages.install("../uranium/uranium-plus[vscode]", develop=True)
import uranium_plus

current_build.config.update(
    {
        "uranium-plus": {
            "module": "tycho",
            "publish": {"additional_args": ["--release"]},
            "test": {
                "packages": ["pytest-aiohttp", "pytest-xdist", "gunicorn", "asynctest"]
            },
        }
    }
)

uranium_plus.bootstrap(current_build)


@current_build.task
def build_statics(build):
    build.executables.run(["npm", "install", build.root])
    build.executables.run(["gulp", "build"])


# current_build.tasks.append("main", "build_statics")


@current_build.task
def start_db(build):
    stop_db(build)
    build.executables.run(
        ["/bin/bash", "-c", ("docker run -p 27017:27017 --name tycho-db" " -d mongo"),]
    )


@current_build.task
def stop_db(build):
    # using subprocess.call as we don't want to
    # error out if the container is not running.
    subprocess.call(["/bin/bash", "-c", "docker stop tycho-db"])
    subprocess.call(["/bin/bash", "-c", "docker rm tycho-db"])


current_build.tasks.prepend("test", "start_db")
current_build.tasks.append("test", "stop_db")


@current_build.task
@task_requires("build_docs")
def copy_docs(build):
    """ copy documentation into the application directory. This allows
    the docs to be packaged with the app itself.
    """
    doc_dir = os.path.join(build.root, build.config["uranium-plus"]["module"], "docs")
    if os.path.exists(doc_dir):
        shutil.rmtree(doc_dir)
    shutil.copytree(
        os.path.join(build.sandbox_root, "build", "docs"),
        os.path.join(build.root, build.config["uranium-plus"]["module"], "docs"),
    )


current_build.tasks.append("main", "copy_docs")
