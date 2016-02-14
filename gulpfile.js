var gulp = require('gulp');
var sass = require('gulp-sass');
var cssnano = require('gulp-cssnano');

gulp.task('default', function(){

  gulp.task('sass', function(){
    return gulp.src('scarf/static/assets/sass/*.scss')
      .pipe(sass()) // Converts Sass to CSS with gulp-sass
      .pipe(gulp.dest('scarf/static/'))
  });

  gulp.task('cssnano', function() {
    return gulp.src('scarf/static/*.css')
      .pipe(cssnano())
      .pipe(gulp.dest('scarf/static/min/'));
  });
  gulp.watch('scarf/static/assets/sass/*.scss', ['sass']);
  gulp.watch('scarf/static/*.css', ['cssnano']);
});
