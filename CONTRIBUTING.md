# Contributing

## Running Tests

As with all orbital python apps, tests can be executed by running:

    ./uranium test

Running the tests requires a mongodb instance running locally, at port 21017. This is handled for you during ./uranium test by bringing up a docker container. You can also bring one up by hand with:

    $ docker pull mongo
    $ docker run -d -p 127.0.0.1:27017:27017 mongo
