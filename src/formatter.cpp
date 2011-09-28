/*
   Copyright 2011 Carl Anderson

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
*/

#include "formatter.hpp"

#include <algorithm>
#include <iomanip>
#include <vector>

#include "database.hpp"
#include "logger.hpp"


using namespace ash;
using namespace std;


/**
 * A mapping of name to singleton instance of all initialized Formatters.
 */
map<string, Formatter *> Formatter::instances;


/**
 * Returns the Formatter singleton matching the argument name, if found;
 * otherwise returns NULL.
 */
Formatter * Formatter::lookup(const string & name) {
  return instances.find(name) == instances.end() ? 0 : instances[name];
}


/**
 * Returns a map of formatter names to descriptions.
 */
map<string, string> Formatter::get_desc() {
  map<string, string> rval;
  map<string, Formatter *>::iterator i, e;

  for (i = instances.begin(), e = instances.end(); i != e; ++i) {
    if (i -> second)
      rval[i -> first] = i -> second -> description;
  }
  return rval;
}


/**
 * Creates a Formatter, making sure it has a unique name among all Formatters.
 */
Formatter::Formatter(const string & n, const string & d)
  : name(n), description(d), do_show_headings(true)
{
  if (lookup(name)) {
    LOG(FATAL) << "Conflicting formatters declared: " << name;
  }
  instances[name] = this;
}


/**
 * Destroys this formatter.
 */
Formatter::~Formatter() {
  instances[name] = 0;
}


/**
 * Sets the internal state controlling whether headings are shown or not.
 */
void Formatter::show_headings(bool show) {
  do_show_headings = show;
}


/**
 * Makes this Formatter avaiable for use within the program.
 */
void SpacedFormatter::init() {
  static SpacedFormatter instance("aligned",
    "Columns are aligned and separated with spaces.");
}


/**
 * Returns the maximum widths required for each column in a result set.
 */
vector<size_t> get_widths(const ResultSet * rs, bool do_show_headings) {
  vector<size_t> widths;
  const size_t XX = 4;  // The number of spaces between columns.

  // Initialize with the widths of the headings.
  size_t c = 0;
  ResultSet::HeadersType::const_iterator i, e;
  for (i = (rs -> headers).begin(), e = (rs -> headers).end(); i != e; ++i, ++c)
    if (do_show_headings)
      widths.push_back(XX + i -> size());
    else
      widths.push_back(XX);

  // Limit the width of columns containing very wide elements.
  size_t max_w = 80;  // TODO(cpa): make this a flag.

  // Loop ofer the rs.data looking for max column widths.
  for (size_t r = 0; r < rs -> rows; ++r) {
    for (size_t c = 0; c < rs -> columns; ++c) {
      widths[c] = max(widths[c], min(max_w, XX + (rs -> data[r][c]).size()));
    }
  }

  return widths;
}

/**
 * Calculates the ideal width for each column and inserts column data
 * left-aligned and separated by spaces.
 */
void SpacedFormatter::insert(const ResultSet * rs, ostream & out) const {
  if (!rs) return;  // Sanity check.

  vector<size_t> widths = get_widths(rs, do_show_headings);

  // Print the headings, if not suppressed.
  if (do_show_headings) {
    size_t c = 0;
    ResultSet::HeadersType::const_iterator i, e;
    for (i = (rs -> headers).begin(), e = (rs -> headers).end(); i != e; ++i)
      out << left << setw(widths[c++]) << *i;
    out << endl;
  }

  // Iterate over the data once more, printing.
  for (size_t r = 0; r < rs -> rows; ++r) {
    for (size_t c = 0; c < rs -> columns; ++c) {
      out << left << setw(widths[c]) << (rs -> data)[r][c];
    }
    out << endl;
  }
}


/**
 * Inserts a ResultSet with all values delimited by a common delimiter.
 */
void insert_delimited(const ResultSet * rs, ostream & out, const string & d,
                      const bool do_show_headings)
{
  if (!rs) return;

  const ResultSet::HeadersType & headers = rs -> headers;
  ResultSet::HeadersType::const_iterator i, e;

  if (do_show_headings) {
    size_t c = 0;
    for (i = headers.begin(), e = headers.end(); i != e; ++i, ++c)
      // Don't add a delimiter after the last column.
      out << *i << (c + 1 < rs -> columns ? d : "");
    out << endl;
  }

  // Loop ofer the rs.data inserting delimited text.
  for (size_t r = 0; r < rs -> rows; ++r) {
    for (size_t c = 0; c < rs -> columns; ++c) {
      out << rs -> data[r][c] << (c + 1 < rs -> columns ? d : "");
    }
    out << endl;
  }
}


/**
 * Makes this Formatter avaiable for use within the program.
 */
void CsvFormatter::init() {
  static CsvFormatter instance("csv",
    "Columns are comma separated with strings quoted.");
}


/**
 * Inserts data separated by commas.
 */
void CsvFormatter::insert(const ResultSet * rs, ostream & out) const {
  insert_delimited(rs, out, ",", do_show_headings);
}


/**
 * Makes this Formatter avaiable for use within the program.
 */
void NullFormatter::init() {
  static NullFormatter instance("null",
    "Columns are null separated with strings quoted.");
}


/**
 * Inserts data separated by \0 characters.
 */
void NullFormatter::insert(const ResultSet * rs, ostream & out) const {
  insert_delimited(rs, out, string("\0", 1), do_show_headings);
}


/**
 * Makes this Formatter avaiable for use within the program.
 */
void GroupedFormatter::init() {
  static GroupedFormatter instance("auto",
    "Automatically group redundant values.");
}


/**
 * Determines how many levels should be auto-grouped.
 */
int get_grouped_level_count(const ResultSet * rs, const vector<size_t> & widths)
{
  if (!rs) return 0;  // Sanity check.

  size_t width = 0, length = rs -> rows;
  for (size_t i = 0, e = widths.size(); i != e; ++i) width += widths[i];

  size_t levels = 0;
  
  string prev;
  for (size_t c = 0, cols = rs -> columns; c < cols; ++c) {
    prev = "";
    size_t proposed_len = length;
    for (size_t r = 0, rows = rs -> rows; r < rows; ++r) {
      if (prev != rs -> data[r][c]) {
        ++proposed_len;
        prev = rs -> data[r][c];
      }
    }
    size_t XX = 4;
    size_t proposed_width = max(width - widths[c], widths[c]) + XX * (levels + 1);
    if (width * length < proposed_width * proposed_len) {
      LOG(DEBUG) << "auto-grouping formatter detected optimal level: " << levels;
      return levels;
    }
    ++levels;
    width = proposed_width;
    length = proposed_len;
  }
  return levels;
}


/**
 * Inserts auto-grouped history, starting with the leftmost columns.
 */
void GroupedFormatter::insert(const ResultSet * rs, ostream & out) const {
  if (!rs) return;  // Sanity check.

  vector<size_t> widths = get_widths(rs, do_show_headings);
  size_t levels = get_grouped_level_count(rs, widths);

  if (do_show_headings) {
    ResultSet::HeadersType::const_iterator h = rs -> headers.begin();
    for (size_t c = 0, cols = rs -> columns; c < cols; ++c) {
      if (c < levels) {
        out << *h << "\n";
        for (size_t i = c + 1; i > 0; --i) out << "    ";
      } else {
        if (c < cols - 1) {
          out << left << setw(widths[c]) << *h;
        } else {
          out << *h;
        }
      }
      ++h;
    }
    out << endl;
  }
  
  vector<string> prev(levels);
  string value;
  for (size_t r = 0, rows = rs -> rows; r < rows; ++r) {
    for (size_t c = 0, cols = rs -> columns; c < cols; ++c) {
      value = rs -> data[r][c];
      if (c < levels) {
        if (value != prev[c] || r == 0) {
          // The value has not been grouped, 
          out << value;
          if (c < cols - 1) {
            // Since it's not the final column, wrap the line and indent
            // to the next level in preparation for the next value.
            out << "\n";
            for (size_t i = c + 1; i > 0; --i) out << "    ";
            for (size_t i = c; i < levels; ++i) prev[i] = "";
          }
          prev[c] = value;
        } else {
          // The value has been grouped, only print the indent.
          out << "    ";
        }
      } else {
        // Normal (non-grouped) case.
        if (c < cols - 1) {
          out << left << setw(widths[c]) << value;
        } else {
          out << value;
        }
      }
    }
    out << endl;
  }
}

