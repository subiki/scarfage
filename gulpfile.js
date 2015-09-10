var gulp = require('gulp');
var sass = require('gulp-sass');

gulp.task('styles', function() {
    gulp.src('./scarf/precompile/scss/*.scss')
        .pipe(sass().on('error', sass.logError))
        .pipe(gulp.dest('./scarf/static/css/'))
});

//Watch task
gulp.task('default',function() {
    gulp.watch('./scarf/precompile/scss/*.scss',['styles']);
});
