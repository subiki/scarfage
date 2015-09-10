var gulp = require('gulp');
var sass = require('gulp-sass');

// var process     = require('child_process');

/* START FLASK SERVER
gulp.task('flask', function(){
  var spawn = process.spawn;
  console.info('Starting flask server');
  var PIPE = {stdio: 'inherit'};
  spawn('python', ['../run.py','runserver'], PIPE);
});
*/

/* COMPILE SCSS ON CHANGE */
gulp.task('styles', function() {
    gulp.src('./scarf/precompile/scss/*.scss')
        .pipe(sass().on('error', sass.logError))
        .pipe(gulp.dest('./scarf/static/css/'))
});

/* WATCH FOR CHANGES ON SCSS */
gulp.task('default',function() {
  gulp.watch('./scarf/precompile/scss/*.scss',['styles']);
});
