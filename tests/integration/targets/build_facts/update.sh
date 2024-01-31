#!/usr/bin/env bash

for i in $(seq 1 1); do
  file_to_compare="/tmp/ansible_it_build_facts_$i.yml"
  expected_file="tests/$i/expected.yml"

  diff_output=$(diff "$file_to_compare" "$expected_file")

  if [ -n "$diff_output" ]; then
    echo "----------------------- test $i --------------------------"
      echo "Differences found:"
      echo "$diff_output"

      read -p "Do you want to overwrite $expected_file with $file_to_compare? (y/n) " -r
      if [[ $REPLY =~ ^[Yy]$ ]]; then
          cp "$file_to_compare" "$expected_file"
      else
          echo "Copy operation aborted."
      fi
    echo "----------------------------------------------------------"
  fi
done
echo "Done"
