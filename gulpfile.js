var gulp = require('gulp');
var sass = require('gulp-sass');
var cssnano = require('gulp-cssnano');
var concat = require('gulp-concat');

gulp.task('default', function(){

  gulp.task('sass', function(){
    return gulp.src('scarf/static/assets/sass/*.scss')
      .pipe(sass()) // Converts Sass to CSS with gulp-sass
      .pipe(concat('style.min.css'))
      .pipe(cssnano())
      .pipe(gulp.dest('scarf/static/'))
  });

  gulp.watch('scarf/static/assets/sass/*css', ['sass']);
});
