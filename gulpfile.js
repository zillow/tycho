var gulp = require('gulp');
var gutil = require('gulp-util');
var less = require('gulp-less');
var mocha = require('gulp-mocha');
var uglify = require('gulp-uglify');
var babel = require('gulp-babel');
var webpackStream = require('webpack-stream');
var webpack = require('webpack');
var path = require('path');

/**
Set up paths for loading js and test files
**/
var pathConfig = {
    jsSource: 'src/js/**/*.js',
    jsTarget: 'target/js',
    src: path.join(__dirname, '/src/js')
};

pathConfig.alljs = [
    path.join(pathConfig.src, '**/*.js'),
    '!**/__test__/**'
];

pathConfig.alltests = [
    path.join(pathConfig.src, '**/test-*.js')
];

gulp.task('sync-js', function () {
    console.log(pathConfig.src);
    console.log(pathConfig.jsSource);
    return gulp.src(pathConfig.jsSource)
        .pipe(babel({ presets: ['es2015'] }))
        .pipe(gulp.dest(pathConfig.jsTarget));
});

gulp.task('bundle-js', ['sync-js'], function() {
    return gulp.src(pathConfig.jsTarget + '/GraphApp.js')
        .pipe(webpackStream({
            output: {
                filename: "ets.js"
            },
            plugins: [
                new webpack.optimize.UglifyJsPlugin({
                    compress: {
                        warnings: false
                    },
                    mangle: {
                        except: ['$super', '$', 'exports', 'require']
                    }
                })
            ],
        }, webpack))
        .pipe(gulp.dest('event_tracking/static/js'));
});

gulp.task('bundle-js-dev', ['sync-js'], function() {
    return gulp.src(pathConfig.jsTarget + '/GraphApp.js')
        .pipe(webpackStream({
            output: {
                filename: "ets.js"
            }
        }))
        .pipe(gulp.dest('event_tracking/static/js'));
});

gulp.task('uglify-js', ['bundle-js'], function () {
    // should only run on full gulp build to avoid perf penalty while developing
    var combined = combiner.obj([
        gulp.src('zon/static/js/zon.js'),
        uglify({
            // code-renaming is not playing nice
            mangle: false
        }),
        gulp.dest('zon/static/js')
        ]);
        return combined;
});

gulp.task('compile-less', function () {
    return gulp.src('src/less/**/*.less')
        .pipe(less({
            pathConfig: [ path.join(__dirname, 'target') ]
        }))
        .pipe(gulp.dest('event_tracking/static/css'));
});

gulp.task('build', [
    'sync-js', 'bundle-js', 'compile-less'
]);

gulp.task('build-dev', [
    'sync-js', 'bundle-js-dev', 'compile-less'
]);

gulp.task('watch', function () {
    var jsxwatcher = gulp.watch([pathConfig.jsSource], ['build']);
    var lesswatcher = gulp.watch(['src/less/**/*.less'], ['compile-less']);

    jsxwatcher.on('change', function (event) {
        console.log('File ' + event.path + ' was ' + event.type + ', running tasks...');
    });

    lesswatcher.on('change', function (event) {
        console.log('File ' + event.path + ' was ' + event.type + ', running tasks...');
    });

    failOnError = false;
});

/**
 * Run mocha unit tests
 */
gulp.task('test', function (cb) {
    return gulp.src(pathConfig.alltests, {read: false})
            .pipe(mocha({
                reporter: 'spec'
            }))
            .on('error', function (err) {
                if (!failOnError) {
                    // Eat the error
                    gutil.log('mocha-test', err);
                    this.emit('end');
                }
            });
});

/**
 * Re-runs tests when changes are made to a unit test file (for development).
 */
gulp.task('watch-test', function () {
    failOnError = false;
    gulp.watch(pathConfig.alltests, ['test']);
});
