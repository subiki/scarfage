#!/bin/bash

echo "$0 Starting..."
dir="$(dirname $0)"
echo "$dir"

#echo "Activating venv..."
#. "${dir}"/.venv/bin/activate

exclude="favicon.png robots.txt .gitignore"

find "$dir" -name .gitignore -exec echo rm {} \;
dep=$(date | sha256sum | head -c30)

echo "Deployment hash will be $dep"

for file in $(find "${dir}/scarf/static/" -not -type d); do
    filedir=$(dirname "$file")
    basename=$(basename "$file")
    newname="$dep-$basename"

    for efile in $exclude; do [[ "$basename" == "$efile" ]] && continue 2; done

    echo "Mutating $file to $newname"
    mv "$file" "$filedir/$newname"

    find -L "${dir}/scarf/templates/" -not -type d -exec sed -i "s#/static/$basename#/static/$newname#g" {} \;
done

echo "$0 Finished!"
