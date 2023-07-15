# 4DML Transformation Utility v0.691 Reference Manual
Silas S. Brown, 26 October 2006

# 1. Introduction
The 4DML transformation utility can be used for the rapid prototyping of complex structural transformations on data.

4DML is a data structure that can represent both tree-like and matrix-like structures in any number of dimensions and supports multiple independent structures over the same data. The transformation utility converts data into 4DML and then reads it out in the order dictated by a 'model', which shows the desired structure of the output.

# 2. Invocation
This describes the invocation and command-line arguments of the 4DML transformation utility.
## 2.1. Specifying the input
### 2.1.1. -input (Read XML)
Read the input from an XML file.  The next argument specifies the input filename; a filename of - represents the standard input.
### 2.1.2. -spaninput (Read XML with COLSPAN/ROWSPAN)
Read the input from an XML file, recognising ROWSPAN and COLSPAN attributes according to the semantics of HTML tables. Position numbers are adjusted so that the position number of an element reflects which column it begins in, taking ROWSPAN and COLSPAN into account.  The next argument specifies the input filename; a filename of - represents the standard input.
### 2.1.3. -inpspec (Read XML with overlaps)
Read the input from an XML file, but recognise the special attributes for overlapping markup.  The next argument specifies the input filename; a filename of - represents the standard input.
### 2.1.4. -spaninpspec (Read XML with colspan/rowspan and overlaps)
This option is a combination of -spaninput and -inpspec.
### 2.1.5. -minput (Read MML)
Read the input from an MML (Matrix Markup Language) file. The next argument specifies the input filename; a filename of - represents the standard input.

The Unix installation script also sets up a command 'mml2xml', to convert MML (on standard input) into XML.
### 2.1.6. -link (Add links to input)
Automatically adds ''link'' elements that join together any two or more strings that happen to be the same.  These elements are independent from the rest of the markup and can be ignored if not needed.  For a description of why they might be useful, see the documentation for the ''broaden'' model parameter (under ''Model parameters'' and ''Adjusting the choice of elements processed'').

The link elements will be named according to what is specified here, so you can say ''-link autolink'' if you want them to be called ''autolink'', or ''-link link'' if you want them to be called ''link''.  Choose something that does not conflict with the other names you are using.

If the model doesn't need this parameter (and if you wrote it then you should know if it does), specifying this parameter should be harmless, but it slows the program down and takes more memory.
## 2.2. Specifying the model
### 2.2.1. -model (XML model)
Read the model from an XML file.  The next argument specifies the input filename; a filename of - represents the standard input.
### 2.2.2. -cmod (CML on command line)
The next argument specifies the model in CML (Compact Model Language) as a string.
### 2.2.3. -cmodel (Embedded CML)
Read the model from a text file with embedded CML (Compact Model Language).  The next argument specifies the filename; a filename of - represents the standard input.

The Unix installation script also sets up a command 'cml2xml', to convert embedded CML (on standard input) into XML.
### 2.2.4. -pmodel (Python module)
Load a Python module for introspection, and derive the model from that.  The next argument specifies the Python module to load.  A full pathname is also acceptable.
### 2.2.5. -python (Auxiliary Python module)
Load a Python module, but do not introspect it; the functions in the module are accessible from the 'python' model parameter.  The model itself should be loaded from another format (such as CML).
### 2.2.6. Model as part of the input
If no model is specified on the command line then it is looked for in the input, under an element called 'model' (the operation 'model number=1' will be executed to extract it).  The model is assumed to be in CML regardless of the input format.  The element 'model' is not removed from the input.
## 2.3. Specifying the function
### 2.3.1. -transform (Perform transform)
Perform a model transform and output the result.  This is the default.
### 2.3.2. -gui (Run GUI)
Run the GUI instead of performing any transform at the command line.
### 2.3.3. -guidebug (Run GUI with call trace)
Run the GUI, and perform a ''Capture call tree'' operation to show the details of how the model was interpreted.
## 2.4. Output
Output is always written to the standard output.  You can use the shell to redirect it to a file or to pipe it to another command.
## 2.5. Improving the speed
If the problem is that you are running out of RAM, then try setting the no_psyco environment variable before running 4DML.  This suppresses the use of Psyco (an optimiser which can often take lots of RAM) and also suppresses the use of partial-result caches (these caches save time provided that enough RAM is available, but if RAM is in short supply, or you are transforming a very large dataset, then it's best not to have them).

The Unix installation script installs other commands besides 4dml, including:

* 4dml2.2: Runs 4DML using Python version 2.2.  This is a hack to support systems that have more than one version of Python installed and that have 2.1 as the default, e.g. Debian Woody.  If Psyco (the Python Specialising Compiler) is installed, 4DML can take advantage of it, but only if it is running on Python version 2.2 or above.
* fast4dml: Runs 4DML with no error checking.  This may give a little additional speed, but any errors could go undetected, leading to unusual results.  (Bug: This currently assumes that python is located in /usr/bin)
* fast4dml2.2: A combination of both of the above.

Additionally, it is possible to instruct the 4DML utility to send its fourspace to a faster computer (via SSH or similar) and perform processing on that.  This has not yet been documented.
## 2.6. Internationalisation and support for many characters
The 4DML transformation utility assumes by default that its input is encoded in UTF-8.  Output is also in UTF-8.  If necessary, a utility such as *tcs* can be used to translate between this and other encodings (such as GB2312, Big5, JIS, etc).

# 3. Input in XML
Each element in the XML is given a depth number and a position number.  The top-level element is at depth 1, and position numbers begin again at 1 with each level of recursion.  For example, in the markup:

    <TR><TD/><TD/></TR>
    <TR><TD/><TD/></TR>

position numbers are assigned as follows:

    <TR p=1><TD p=1/><TD p=2/></TR>
    <TR p=2><TD p=1/><TD p=2/></TR>

Hence, a ''for each TD'' operation, if not enclosed by ''for each TR'', will cut across the TR elements when grouping the TD elements together.
## 3.1. Special attributes for overlapping markup
These are not recognised unless specifically asked for on the command line.

The attribute '_InitPos' sets the position number of this element, overriding the position number that would have been given to it by default.

Elements that have the special attributes described below should be empty.  The name of the element should correspond with the name of a higher-level element that is in progress at that point, and the attributes specify directives for manipulating the position number of that higher-level element, while it is in progress.  Hence the higher-level element can be divided into two without interrupting the intervening markup.  The element with special attributes does not itself appear in the 4DML.

The attribute '_IncrementPos' causes the position number of the higher-level element to be incremented.

The attribute '_SetPos' causes the position number of the higher-level element to be set to the given value.

The attribute '_Rename' changes the name of the higher-level element to the one given.  This should not normally be used.

The attribute '_Unfinished' signifies that we are not through with adjusting positioning information.  This means that, if there is another element following with no intervening character data, then no empty element will be recorded to note the new position number at this point.  If you wish to change the position numbers of several higher-level elements in one operation then it is generally a good idea to use the '_Unfinished' attribute so as to prevent an inconsistent state being recorded.

# 4. Input in MML (Matrix Markup Language)
## 4.1. MML basics
Matrix Markup Language (MML) is a text-based language that can represent structure in several ways, such as by using ''begin''/''end'' pairs, ''element: value'' lines, and matrix-like blocks.  It is meant to be a convenient way of hand-coding data that is both hierarchical and matrix-like in structure.

''begin e'' and ''end e'' cause everything in between to be enclosed in an element named ''e''.  An alternative way of representing this is ''e:'' followed by some text; the rest of the line is treated as the contents of element ''e''. The construct ''advance e'' will cause the position of ''e'' (an element currently in progress) to be advanced, even if it is not the innermost element that is currently in progress.

Files in MML are enclosed in an implicit ''document'' element.

**Note:** When using ''e:'' followed by some text, the rest of the line should be non-empty, otherwise the next non-empty line will be used instead.  (This can be useful when working with very narrow displays.)

## 4.2. Blocks
An MML matrix-like block is enclosed within ''!block'' and ''!endblock''.  Each block has two parts, a header and a body.  The first blank line separates the header from the body.  The header specifies the meaning of the separation symbols that are to be used in the body.  The following constructs can appear in the header:
### 4.2.1. Initial element name
The first word after a ''!block'' can be the name of an element in which the whole block is to be contained, so long as this is not a reserved word (if it is a reserved word then you have to write a ''begin''/''end'' construct around the block instead).
### 4.2.2. have ... as
The construct ''have A as B'' causes the symbol A to be used as a separator, advancing the position number of an element called B.

If there are several ''have...as'' constructs, then they are given increasing depth numbers, and an advancement of a higher-level position number (i.e. lower depth number) causes all positions at lower levels to be reset to 1.

As a special case, the keyword ''paragraph'' matches one or more blank lines; the keyword ''newline'' matches a single newline character, and the keyword ''whitespace'' matches any amount of whitespace.  If they are all used, paragraph, newline and whitespace should be specified in that order, because a new paragraph can be interpreted as new lines, which in turn can be interpreted as whitespace.

The keyword ''character'' causes the input to be split into individual characters (like setting the separator to the empty string); use this with care.

If desired, multiple ''have...as'' constructs can be amalgamated thus: ''have A1 A2 A3... as B1 B2 B3...''
### 4.2.3. also
The word ''also'' can be used to separate independent groups of ''have...as'' constructs.  Changes of positions in one group will not change the positions in the others.  Hence the block's body can represent multiple, independent hierarchies over the same data.
### 4.2.4. special
This can be used to specify special ways of interpreting some operators.  Currently, it can be used as follows:

    special: A maximum 5 per B

Here, it is specified that there are at most 5 elements called A; effectively, all the A's are grouped together into B's, with a maximum of 5 per group.

    special: A label 4 as B

Specifies that the 4th instance of element A should really be called B (rather than A).  Can be useful if you need to define an operator whose parameters are completely different things (although this should be rare).

    special: A switches B

Here the operator A will switch the element B to an arbitrary position.  The position is determined by a mnemonic that occurs after A, before the next space.

For example, if A is / and B is ''project'', then /myprj (followed by whitespace) will cause the following data to be under a ''project'' element with position given by the mnemonic ''myprj'' (the textual mnemonics that you use are automatically given numbers).

This can be a useful shortcut if you are organising a large amount of unsorted data into several categories.

    special: A switches.

(i.e. a dot after ''switches'') is the same as above, except that the B is defined as the same as the mnemonic.  In other words, immediately after you use the operator A, you will specify the name of the element that the following text is to appear under, followed by whitespace.
## 4.3. Emacs major mode
A major mode is available for editing MML files with emacs and xemacs.  This is supplied with 4dml as 4dml.el (will be compiled to 4dml.elc if emacs is available at install time). To install it, you need to put something like this in your emacs init file (remembering to substitute the correct installation directory if necessary):

    (autoload '4dml-mml-mode
    "/usr/local/lib/site-python/4dml/4dml.elc"
    "Major mode for editing 4DML MML files" t)
    (setq auto-mode-alist
    (append '(("\\.mml\\'" . 4dml-mml-mode))
    auto-mode-alist))

The mode should syntax highlight reasonably correctly when loading a file or doing font-lock-fontify-buffer, but might not be so good when actually editing, especially when editing !block constructs, since font-lock only considers one line at a time.  c.f. HTML mode problems in comments etc.  If in doubt, do M-x font-lock-fontify-buffer.

# 5. Model basics
By default, each element in the model will cause the following things to occur.

1. The input is searched for all elements that match the name of the model element.  Only such elements at the highest level at which they occur will be used.  The search will cut across all other markup.
2. The input is divided into groups, one for each distinct element that was found, and the groups are sorted by position number.  Any other markup from the input will be included in each group.
3. Any model code that occurs within the current model element will be executed once for each group.
4. If the model element is empty (a leaf node), then the data from each group is copied to the output, discarding all remaining markup.</OL>

Thus an element X in the model is effectively saying ''for each X''.

Arbitrary text in the model is copied to the output whenever it is encountered.

Model elements can be given attributes (parameters) to specify their behaviour in a more flexible manner; see the section on Model Parameters.

# 6. The Compact Model Language (CML)
CML is a compact markup language for models, which often have elements packed inside each other (i.e. of the form `<x><y><z>`...).  CML makes that kind of hierarchy quicker to type.

Use X/Y/Z to put an element Z within a Y, within an X.

Any element name can be followed by attributes, with whitespace before each attribute.  Attributes take the form name [ =value ] where the text enclosed in [] is optional (value defaults to 1; this is intended for use when the attribute merely has to be present).  Values should be quoted with "..." if they contain any unusual characters.

Use a comma (,) to separate two or more elements that are at the same level.  This has a lower precedence than / but you can use parentheses.

Arbitrary text can appear in quotes in place of an element. It can be enclosed within ]] and [[cml, which imply commas either side of them unless they are being used to specify the value of a parameter; in this case the text can span multiple lines and include any character such as quotes.  When CML is embedded in a text file, the whole file is automatically enclosed within those operators, so the effect is that the CML parts of the file are delineated by [[cml and ]].

Models in CML are enclosed in an implicit ''document'' element, which has implicit attributes ''nomarkup'' and ''no-input''.

# 7. Models as Python Modules
Models can be specified as Python modules that are examined by introspection.  This makes it possible to embed arbitrary Python code within 4DML models.
## 7.1. Syntax
The model will be derived from the Python module by introspection.  A class in the Python module corresponds to an element in the model, and this class can have other classes as members (inner classes) to signify child elements.  Attributes are specified as variables within the class.  For example:

    class paragraph:
       between = "\\par "
       class word:
         between = " "

Any underlines (_) in attributes are changed into hyphens (-).

If necessary, an attribute 'realname' can specify the real name of the model element, should the class have to be named something else (such as to avoid duplication).  If there are several classes (elements) at the same level, then their order may be specified in a list, such as

    order = [ class1, class2, .. ]

after the classes have been defined.  Some kind of order specification is necessary because Python classes are dictionaries; the items are not necessarily stored in the order in which they appear in the source code.

If (and only if) the Python module specifies more than one top-level element, then it is enclosed in an implicit ''document'' element.
## 7.2. Filter methods
These can be used to code arbitrary low-level filters for the data, to be applied during the model transform.

If a class has a method called ''filter'', and it is a leaf node in the model (i.e. it causes data to be copied to the output), then the class will be instantiated, and the ''filter'' method will be called for each string that is to be output (by that particular leaf node).  The ''filter'' method is expected to take the string as an argument and to return a replacement string.
## 7.3. Using hash-bang to execute models
In Unix-based systems, you can use the ''hash-bang'' feature of the kernel to make the Python-based models executable directly.  Some kernels have problems running 4DML with hash-bang (because 4DML is itself a script), but you can use a hack such as:

    #!/bin/bash
    "eval" "exec 4dml -pmodel $0"

Other arguments can be added if desired.

# 8. Model Parameters
These parameters can be added as attributes to any element of a model, to change the behaviour of the model processor with respect to that element or its children.
## 8.1. Changing the markup (XML)
### 8.1.1. rename
Specifies a new name for the element, to be used in the XML output.  This is useful if the nomenclature is different (e.g. `<BAR rename="MEASURE">`).  Element names that are empty (rename="") are accepted; when converting to XML, no markup is output around such elements (an alias for 'rename=""' is 'discard').
### 8.1.2. from
This is an alternative to 'rename'; it specifies the *old* name of the element.  For example, `<BAR rename="MEASURE">` is equivalent to `<MEASURE from="BAR">`.  You might want to use this if you find it easier to specify the desired structure in the element names.

Note that if you use both 'from' and 'rename', the name of the element itself becomes meaningless.
### 8.1.3. allow-empty
Allows the element to be empty in the output.  Normally the element is only included if there is some data in it.  If 'allow-empty' is set then the element will appear in the output whether or not there is data available (although it will not appear if there is a model within it and that model does not cause any output).
### 8.1.4. no-input
If present, specifies that this element is to be copied directly to the output, regardless of the input.  The name of the element itself can be used to specify the name of the output element.  This can be used to specify XML markup that is to appear in the output unconditionally, perhaps enclosing the parts of the output that depend on the input.
### 8.1.5. _
Any parameter beginning with an underline (_) will be copied directly to the output as an attribute, with the underline removed.  This is a way of hard-coding output attributes into the model.
## 8.2. Changing the markup (not XML)
These parameters were designed for producing non-XML markup, but they are also allowed when producing XML markup.
### 8.2.1. nomarkup
Equivalent to setting rename="" for this and all child elements; causes no XML markup to be output.  Can be used for the top-level element when the output is not XML (can also be used for non-XML fragments within an XML document).

If any element under a 'nomarkup' element does have a 'rename' or 'from' attribute, then the 'nomarkup' does not apply to that particular element, although it does apply to its children.  This does not affect whether or not the whole output is treated as XML (if the top-level element is 'nomarkup' then it is treated as plain text, and any elements underneath that have 'rename' or 'from' attributes are written into the text in normal XML syntax).
### 8.2.2. before
Specifies any text that is to be included in the output before the first one of these elements.
### 8.2.3. after
Specifies any text that is to be included in the output after the last one of these elements.
### 8.2.4. between
Specifies any text that is to be included in the output between each of these elements (but not before the first or after the last).
### 8.2.5. group
Specifies any text that is to be included in the output between each of these elements, as an alternative to the 'between' text.  The 'group' text is used instead of the 'between' text every 10th element (the value of 10 can be changed by specifying group-size).  This can be used as a rudimentary way of dividing the elements into groups for readability.
### 8.2.6. group-size
Specifies the number of elements to count before substituting 'group' for 'between' for one element.
### 8.2.7. begin
Specifies any text that is to be included in the output inside each one of these elements, at its beginning.
### 8.2.8. end
Specifies any text that is to be included in the output inside each one of these elements, at its end.
## 8.3. Adjusting the choice of elements processed
### 8.3.1. start-at
Does not process any elements before the specified position number; the first position number is 1.  Note that this is absolute; if the currently-available position numbers start at 3, for example, then start-at=3 will start at the first one.  Use the 'renumber' attribute as well if this is not desirable.
### 8.3.2. end-at
Does not process any elements after the specified position number; the first position number is 1.  Note that this is absolute; if the currently-available position numbers start at 3, for example, then end-at=3 will end at the first one. Use the 'renumber' attribute as well if this is not desirable.
### 8.3.3. number
Sets both start-at and end-at to the given value.  Only elements with the given position will be processed.  See also 'renumber'.
### 8.3.4. renumber
Changes the behaviour of 'start-at', 'end-at' and 'number' so that the position numbers are effectively renumbered. This does not affect any other processing of position numbers.
### 8.3.5. value
Restricts which elements are processed by including only those that have the given value as their contents. This can be used to substitute one value for another.  See also 'other-values'.
### 8.3.6. total
Restricts which elements are processed by including only those that occur exactly the given number of times in the data that is currently under consideration.  This can be used for different processing depending on how many there are.  See also 'other-values'.
### 8.3.7. other-values
Specified immediately after any 'value' or 'total' restrictions; matches only the elements that have not already been matched by the above restrictions.
### 8.3.8. external
Specifies whether ''foreach'' should search the display stack (see below).  A value of "never" avoids searching the display stack; "always" searches *only* the display stack. The default action is to search the display stack only if no result is found in the current data.

Consider the effect of the model

    <SCORE> <PART> <TITLE/> . . .

on the input:

    <SCORE>
       <TITLE> . . </TITLE>
       <PART> . . </PART>
       . . .

The intention here is that each PART bears the TITLE of the SCORE.  However, TITLE's data is outside the scope of the PART element and will therefore not be present in the corresponding subset of the input when PART is processed. It can be reached by searching a display stack of fourspaces that contain all points not present in any of the subspaces generated by the model. Hence, if no TITLEs are found in the PART, then the SCORE will be searched (this search excluding all of the PARTs); if no TITLEs are found there then the next level up will be searched and so on.

Setting external=clear will cause a new display stack to be started for the part of the model that is enclosed by this element.  The effect is to isolate this part of the model from the rest as far as the display stack is concerned.  It is rarely needed.
### 8.3.9. broaden
Specifies that, after ''foreach'' selects an element, it should then select the full extent of that element *from the original fourspace* (not just the subset of it that it was looking at).  Hence the element is ''broadened'' to its full value.

''broaden'' may take a value, corresponding to another element name; if an element matching this latter name exists, and is above the element that ''foreach'' is trying to broaden, then the former element is only broadened within the scope of the latter one.  This should be used to disambiguate cases where ''broaden'' incorrectly 'merges' elements that should have been separate.

One application of the ''broaden'' parameter is in following links, as in:

    pointer/link broaden/id/whole-entry broaden

where an element called 'whole-entry' contains an element called 'id', which contains the same string as referenced elsewhere by one or more elements called 'pointer' (one of which is being inspected at this point in the model).

All links in this manner can be treated as bi-directional many-to-many mappings and read as needed.
## 8.4. Changing the behaviour of child-element processing
### 8.4.1. children-only
Causes only elements that are (direct or indirect) children of the given element to be considered; any markup *above* that element is not included in the subset.
### 8.4.2. sequential
Causes each input element's immediate children to be processed sequentially, rather than being grouped by element name as would normally happen. This will often be used when processing documents that contain a mixture of different types of object in any order (as is the case with XHTML). Setting sequential implies children-only, and also that only an element's immediate children are considered by the next level of the model. As a special case, sequential="cdata" additionally causes any cdata elements (at that level) to be copied from input to output.
### 8.4.3. flatten
Destroy all depth information in the generated subsets. Used when you later want to divide the data in a manner that is depth-independent.  This usually occurs when there are two or more discrete types of data (e.g. words and music) that have some value to synchronise on (e.g. time) but it is not at the same level.  It would be possible to perform a ''flat search'' individually for each element, but usually there are a lot of them so it is easier to ''flatten'' everything.  Note that this can have unexpected effects on data that is hierarchical, such as mathematics.
### 8.4.4. no-strip
The markup that this element identifies is not removed before processing child elements.  For example,

    <X no-strip="1" after="y"> <X number="1" after="z" /> </X>

is equivalent to:

    <X number="1" after="zy" /> <X start-at="2" after="y" />

This can be useful for calling library modules that handle special cases (such as the first element) differently.
### 8.4.5. merge
Causes all elements (subsets) to be merged and processed as one.  Can be useful on occasions.  Can be combined with no-strip to provide a form of conditional processing depending on the number of any given element present, e.g.

    X no-strip number=3 merge / (...)

will execute (...) if and only if there are exactly 3 X's, but will not iterate for each X (you might want to process them in a different order, for example).
### 8.4.6. include-rest
The ''rest'' of the data (i.e. any data that was not covered by an instance of the given element) is normally discarded; setting ''include-rest'' will cause it to be included in *all* of the subsets.  This can be useful if it is needed later, for example, if there is a song with several verses and one copy of the music (or one chorus), and it is desired for each verse to be printed along with the music (or chorus).
### 8.4.7. reverse
Reverses the order of the generated subsets before processing them.  Note that this reversal occurs *after* any selection with 'start-at', 'end-at', 'number' or 'renumber'.
## 8.5. Recursion and subroutines
### 8.5.1. call
This is a means of adding recursion to the model. It behaves as though the model under the previous element named by this parameter is also under the current element.  Both recursive and non-recursive calling is supported.
### 8.5.2. export-code
Causes the child elements of this model element to be available for ''call'' even after this element has finished.  Normally they would go out of scope. ''export-code'' can be used in conjunction with a nonsense element name to write a 'library' of model fragments.
## 8.6. Numbering and alternative markup
### 8.6.1. count
Behaves as though there were an element in the input of the same name as this model element, whose value is the position count of the innermost such element that is currently in progress.  For example, the following CML fragment will begin each 'verse' with a number:

    verse / ( verse count after=".", ...

### 8.6.2. if-changed
Only process this element if its position has changed since last time round the loop.  This is used to read off an alternate set of markup that is independent from the main set of markup.  For example, the CML

    page if-changed / ...

will do something whenever ''page'' changes (which might indicate a physical page break in the original source material that is independent of the logical structure).
## 8.7. Error checking
### 8.7.1. expected
Indicates that the element named in the model here is *expected*, that is, at least one of them should be found in the input at this point, and an error should be raised if not.  (Normally 4DML ignores model elements that are not found, since the model can specify what to do with certain elements *in the event that they exist*.)

Using 'expected' in appropriate places can catch most errors like running the wrong model on the wrong sort of data (e.g. trying to transform mathematics as though it were music).  It can also catch many mismatches between row lengths etc (if you have inputted two or more rows of data and you read them by column, and you say that each column is 'expected' to have something from each of the row types you inputted, then there should be an error if one row is longer than the other).
## 8.8. Miscellaneous
### 8.8.1. wildcard
Specifies an element name that is to be treated as a ''wildcard'' that will match any element name (and will not remove that element from the subset generated).
### 8.8.2. debugdump
Adds the name of this top-level element to its 'begin' attribute.  This can be used for debugging wildcards when using 'nomarkup' (you can specify 'debugdump' to see what the wildcard matches).
### 8.8.3. python
Calls a given Python function on each contents string (not markup string) that is written to the output.  The contents is passed to the named function as a string, and the function's return value (which should also be a string) is used in its place.  This can be used to code arbitrary low-level filters for the data, to be applied during the model transform.

The function named here should be defined in a Python module that is loaded with the '-python' command-line option.

# 9. Author
Copyright 2002-2006 Silas S. Brown (Computer Lab, University of Cambridge, 15 JJ Thompson Avenue, Cambridge UK).

No warranty.
