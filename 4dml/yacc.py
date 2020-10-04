

#    4DML Transformation Utility
#
#    (C) 2002-2006 Silas S. Brown (University of Cambridge Computer Laboratory,
#        Cambridge, UK, http://ssb22.user.srcf.net )
#
#     This program is free software; you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation; either version 2 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program; see the file COPYING.  If not, write to
#     the Free Software Foundation, Inc., 59 Temple Place - Suite 330,
#     Boston, MA 02111-1307, USA.


# downloaded from http://systems.cs.uchicago.edu/ply/
# by ssb22 on 2001-12-12
# MODIFIED: The "Generating SLR parsing table" message is
# now only printed if in debug mode
# MODIFIED: Removed "os.path" dependency (not always avail)
# MODIFIED: If running on java, doesn't check signatures (jythonc hack)

#-----------------------------------------------------------------------------
# ply: yacc.py
#
# Author: David M. Beazley (beazley@cs.uchicago.edu)
#         Department of Computer Science
#         University of Chicago
#         Chicago, IL 60637
#
# Copyright (C) 2001, David M. Beazley
#
# $Header: /cvs/projects/PLY/yacc.py,v 1.44 2001/10/25 15:50:05 beazley Exp $
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
# 
# See the file COPYING for a complete copy of the LGPL.
#
#
# This implements an LR parser that is constructed from grammar rules defined
# as Python functions.  Roughly speaking, this module is a cross between
# John Aycock's Spark system and the GNU bison utility.
#
# Disclaimer:  This is a work in progress. SLR parsing seems to work fairly
# well and there is extensive error checking. LALR(1) is in progress.  The
# rest of this file is a bit of a mess.  Please pardon the dust.
#
# The current implementation is only somewhat object-oriented. The
# LR parser itself is defined in terms of an object (which allows multiple
# parsers to co-exist).  However, most of the variables used during table
# construction are defined in terms of global variables.  Users shouldn't
# notice unless they are trying to define multiple parsers at the same
# time using threads (in which case they should have their head examined).
#-----------------------------------------------------------------------------

__version__ = "1.1"

#-----------------------------------------------------------------------------
#                     === User configurable parameters ===
#
# Change these to modify the default behavior of yacc (if you wish)
#-----------------------------------------------------------------------------

yaccdebug   = 1                # Debugging mode.  If set, yacc generates a
                               # a 'parser.out' file in the current directory

debug_file  = 'parser.out'     # Default name of the debugging file
tab_module  = 'parsetab'       # Default name of the table module
default_lr  = 'SLR'            # Default LR table generation method

error_count = 3                # Number of symbols that must be shifted to leave recovery mode

import re, types, sys, cStringIO, md5 , string #, os.path

# Exception raised for yacc-related errors
class YaccError(Exception):   pass

#-----------------------------------------------------------------------------
#                        ===  LR Parsing Engine ===
#
# The following classes are used for the LR parser itself.  These are not
# used during table construction and are independent of the actual LR
# table generation algorithm
#-----------------------------------------------------------------------------

# This class is used to hold non-terminal grammar symbols during parsing.
# It normally has the following attributes set:
#        .type       = Grammar symbol type
#        .value      = Symbol value
#        .lineno     = Starting line number
#        .endlineno  = Ending line number (optional, set automatically)

class YaccSymbol:
    def __str__(self):    return self.type
    def __repr__(self):   return str(self)

# This class is a wrapper around the objects actually passed to each
# grammar rule.   Index lookup and assignment actually assign the
# .value attribute of the underlying YaccSymbol object.
# The lineno() method returns the line number of a given
# item (or 0 if not defined).   The linespan() method returns
# a tuple of (startline,endline) representing the range of lines
# for a symbol.

class YaccSlice:
    def __init__(self,s):
        self.slice = s
        self.pbstack = []

    def __getitem__(self,n):
        return self.slice[n].value

    def __setitem__(self,n,v):
        self.slice[n].value = v

    def lineno(self,n):
        return getattr(self.slice[n],"lineno",0)

    def linespan(self,n):
        startline = getattr(self.slice[n],"lineno",0)
        endline = getattr(self.slice[n],"endlineno",startline)
        return startline,endline

    def pushback(self,n):
        if n <= 0:
            raise ValueError, "Expected a positive value"
        if n > (len(self.slice)-1):
            raise ValueError, "Can't push %d tokens. Only %d are available." % (n,len(self.slice)-1)
        for i in range(0,n):
            self.pbstack.append(self.slice[-i-1])

# The LR Parsing engine.   This is defined as a class so that multiple parsers
# can exist in the same process.  A user never instantiates this directly.
# Instead, the global yacc() function should be used to create a suitable Parser
# object. 

class Parser:
    def __init__(self,magic=None):

        # This is a hack to keep users from trying to instantiate a Parser
        # object directly.

        if magic != "xyzzy":
            raise YaccError, "Can't instantiate Parser. Use yacc() instead."

        # Reset internal state
        self.productions = None          # List of productions
        self.errorfunc   = None          # Error handling function
        self.action      = { }           # LR Action table
        self.goto        = { }           # LR goto table
        self.require     = { }           # Attribute require table
        self.method      = "Unknown LR"  # Table construction method used

    def errok(self):
        self.errorcount = 0

    def restart(self):
        del self.statestack[:]
        del self.symstack[:]
        sym = YaccSymbol()
        sym.type = '$'
        self.symstack.append(sym)
        self.statestack.append(0)
        self.recover()
        
    def parse(self,input=None,lexer=None,debug=0):
        lookahead = None                 # Current lookahead symbol
        lookaheadstack = [ ]             # Stack of lookahead symbols
        actions = self.action            # Local reference to action table
        goto    = self.goto              # Local reference to goto table
        prod    = self.productions       # Local reference to production list
        pslice  = YaccSlice(None)        # Slice object passed to grammar rules
        self.errorcount = 0              # Used during error recovery
        
        # If no lexer was given, we will try to use the lex module
        if not lexer:
            import lex as lexer

        # If input was supplied, pass to lexer
        if input:
            lexer.input(input)

        # Tokenize function
        get_token = lexer.token

        statestack = [ ]                # Stack of parsing states
        self.statestack = statestack
        symstack   = [ ]                # Stack of grammar symbols
        self.symstack = symstack

        errtoken   = None               # Err token

        # The start state is assumed to be (0,$)
        statestack.append(0)
        sym = YaccSymbol()
        sym.type = '$'
        symstack.append(sym)
        
        while 1:
            # Get the next symbol on the input.  If a lookahead symbol
            # is already set, we just use that. Otherwise, we'll pull
            # the next token off of the lookaheadstack or from the lexer
            if not lookahead:
                if not lookaheadstack:
                    lookahead = get_token()     # Get the next token
                else:
                    lookahead = lookaheadstack.pop()
                if not lookahead:
                    lookahead = YaccSymbol()
                    lookahead.type = '$'
            if debug:
                print "%-20s : %s" % (lookahead, [xx.type for xx in symstack])

            # Check the action table
            s = statestack[-1]
            ltype = lookahead.type
            t = actions.get((s,ltype),None)

            if t is not None:
                if t > 0:
                    # shift a symbol on the stack
                    if ltype == '$':
                        # Error, end of input
                        print "yacc: Parse error. EOF"
                        return
                    statestack.append(t)
                    symstack.append(lookahead)
                    lookahead = None

                    # Decrease error count on successful shift
                    if self.errorcount > 0:
                        self.errorcount -= 1
                        
                    continue
                
                if t < 0:
                    # reduce a symbol on the stack, emit a production
                    p = prod[-t]
                    pname = p.name
                    plen  = p.len

                    # Get production function
                    sym = YaccSymbol()
                    sym.type = pname       # Production name
                    sym.value = None

                    if plen:
                        targ = symstack[-plen-1:]
                        targ[0] = sym
                        try:
                            sym.lineno = targ[1].lineno
                            sym.endlineno = getattr(targ[-1],"endlineno",targ[-1].lineno)
                        except AttributeError:
                            sym.lineno = 0
                        del symstack[-plen:]
                        del statestack[-plen:]
                    else:
                        sym.lineno = 0
                        targ = [ sym ]
                    pslice.slice = targ
                    pslice.pbstack = []
                    # Call the grammar rule with our special slice object
                    p.func(pslice)

                    # Validate attributes of the resulting value attribute
#                  if require:
#                      try:
#                          t0 = targ[0]
#                          r = Requires.get(t0.type,None)
#                          t0d = t0.__dict__
#                          if r:
#                              for field in r:
#                                  tn = t0
#                                  for fname in field:
#                                      try:
#                                          tf = tn.__dict__
#                                          tn = tf.get(fname)
#                                      except StandardError:
#                                          tn = None
#                                      if not tn:
#                                          print "%s:%d. Rule %s doesn't set required attribute '%s'" % \
#                                                (p.file,p.line,p.name,".".join(field))
#                      except TypeError,LookupError:
#                          print "Bad requires directive " % r
#                          pass


                    # If there was a pushback, put that on the stack
                    if pslice.pbstack:
                        lookaheadstack.append(lookahead)
                        for _t in pslice.pbstack:
                            lookaheadstack.append(_t)
                        lookahead = None

                    symstack.append(sym)
                    statestack.append(goto[statestack[-1],pname])
                    continue

                if t == 0:
                    n = symstack[-1]
                    return getattr(n,"value",None)

            if t == None:
                # We have some kind of parsing error here.  To handle this,
                # we are going to push the current token onto the tokenstack
                # and replace it with an 'error' token.  If there are any synchronization
                # rules, they may catch it.
                #
                # In addition to pushing the error token, we call call the user defined p_error()
                # function if this is the first syntax error.   This function is only called
                # if errorcount == 0.

                if not self.errorcount:
                    self.errorcount = error_count
                    errtoken = lookahead
                    if errtoken.type == '$':
                        errtoken = None               # End of file!
                    if self.errorfunc:
                        global errok,token,restart
                        errok = self.errok        # Set some special functions available in error recovery
                        token = get_token
                        restart = self.restart
                        tok = self.errorfunc(errtoken)
                        del errok, token, restart   # Delete special functions
                        
                        if not self.errorcount:
                            # User must have done some kind of panic mode recovery on their own.  The returned token
                            # is the next lookahead
                            lookahead = tok
                            errtoken = None
                            continue
                    else:
                        if errtoken:
                            if hasattr(errtoken,"lineno"): lineno = lookahead.lineno
                            else: lineno = 0
                            if lineno:
                                print "yacc: Syntax error at line %d, token=%s" % (lineno, errtoken.type)
                            else:
                                print "yacc: Syntax error, token=%s" % errtoken.type
                        else:
                            print "yacc: Parse error in input. EOF"
                            return

                else:
                    self.errorcount = error_count
                
                # case 1:  the statestack only has 1 entry on it.  If we're in this state, the
                # entire parse has been rolled back and we're completely hosed.   The token is
                # discarded and we just keep going.

                if len(statestack) <= 1 and lookahead.type != '$':
                    lookahead = None
                    errtoken = None
                    # Nuke the pushback stack
                    del lookaheadstack[:]
                    continue

                # case 2: the statestack has a couple of entries on it, but we're
                # at the end of the file. nuke the top entry and generate an error token

                # Start nuking entries on the stack
                if lookahead.type == '$':
                    # Whoa. We're really hosed here. Bail out
                    return 

                if lookahead.type != 'error':
                    sym = symstack[-1]
                    if sym.type == 'error':
                        # Hmmm. Error is on top of stack, we'll just nuke input
                        # symbol and continue
                        lookahead = None
                        continue
                    t = YaccSymbol()
                    t.type = 'error'
                    if hasattr(lookahead,"lineno"):
                        t.lineno = lookahead.lineno
                    t.value = lookahead
                    lookaheadstack.append(lookahead)
                    lookahead = t
                else:
                    symstack.pop()
                    statestack.pop()

                continue

            # Call an error function here
            raise RuntimeError, "yacc: internal parser error!!!\n"

# -----------------------------------------------------------------------------
#                          === Parser Construction ===
#
# The following functions and variables are used to implement the yacc() function
# itself.   This is pretty hairy stuff involving lots of error checking,
# construction of LR items, kernels, and so forth.   Although a lot of
# this work is done using global variables, the resulting Parser object
# is completely self contained--meaning that it is safe to repeatedly
# call yacc() with different grammars in the same application.
# -----------------------------------------------------------------------------
        
# -----------------------------------------------------------------------------
# validate_file()
#
# This function checks to see if there are duplicated p_rulename() functions
# in the parser module file.  Without this function, it is really easy for
# users to make mistakes by cutting and pasting code fragments (and it's a real
# bugger to try and figure out why the resulting parser doesn't work).  Therefore,
# we just do a little regular expression pattern matching of def statements
# to try and detect duplicates.
# -----------------------------------------------------------------------------

def validate_file(filename):
    # base,ext = os.path.splitext(filename)
    # if ext != '.py': return 1          # No idea. Assume it's okay.
    if filename[-3:] != '.py': return 1

    try:
        f = open(filename)
        lines = f.readlines()
        f.close()
    except IOError:
        return 1                       # Oh well

    # Match def p_funcname(
    fre = re.compile(r'\s*def\s+(p_[a-zA-Z_0-9]*)\(')
    counthash = { }
    linen = 1
    noerror = 1
    for l in lines:
        m = fre.match(l)
        if m:
            name = m.group(1)
            prev = counthash.get(name)
            if not prev:
                counthash[name] = linen
            else:
                print "%s:%d: Function %s redefined. Previously defined on line %d" % (filename,linen,name,prev)
                noerror = 0
        linen += 1
    return noerror

# This function looks for functions that might be grammar rules, but which don't have the proper p_suffix.
def validate_dict(d):
    for n,v in d.items(): 
        if n[0:2] == 'p_' and isinstance(v,types.FunctionType): continue
        if n[0:2] == 't_': continue

        if n[0:2] == 'p_':
            print "yacc: Warning. '%s' not defined as a function" % n
        if isinstance(v,types.FunctionType) and v.func_code.co_argcount == 1:
            try:
                doc = v.__doc__.split(" ")
                if doc[1] == ':':
                    print "%s:%d. Warning. Possible grammar rule '%s' defined without p_ prefix." % (v.func_code.co_filename, v.func_code.co_firstlineno,n)
            except StandardError:
                pass

# -----------------------------------------------------------------------------
#                           === GRAMMAR FUNCTIONS ===
#
# The following global variables and functions are used to store, manipulate,
# and verify the grammar rules specified by the user.
# -----------------------------------------------------------------------------

# Initialize all of the global variables used during grammar construction
def initialize_vars():
    global Productions, Prodnames, Prodmap, Prodempty, Terminals 
    global Nonterminals, First, Follow, Precedence, LRitems
    global Errorfunc, Signature, Requires

    Productions  = [None]  # A list of all of the productions.  The first
                           # entry is always reserved for the purpose of
                           # building an augmented grammar
                        
    Prodnames    = { }     # A dictionary mapping the names of nonterminals to a list of all
                           # productions of that nonterminal.
                        
    Prodmap      = { }     # A dictionary that is only used to detect duplicate
                           # productions.

    Prodempty    = { }     # A dictionary of all productions that have an empty rule
                           # of the form P : <empty>

    Terminals    = { }     # A dictionary mapping the names of terminal symbols to a
                           # list of the rules where they are used.

    Nonterminals = { }     # A dictionary mapping names of nonterminals to a list
                           # of rule numbers where they are used.

    First        = { }     # A dictionary of precomputed FIRST(x) symbols
    
    Follow       = { }     # A dictionary of precomputed FOLLOW(x) symbols

    Precedence   = { }     # Precedence rules for each terminal. Contains tuples of the
                           # form ('right',level) or ('left',level)

    LRitems      = [ ]     # A list of all LR items for the grammar.  These are the
                           # productions with the "dot" like E -> E . PLUS E

    Errorfunc    = None    # User defined error handler

    Signature    = md5.new()   # Digital signature of the grammar rules, precedence
                               # and other information.  Used to determined when a
                               # parsing table needs to be regenerated.

    Requires     = { }     # Requires list

    # File objects used when creating the parser.out debugging file
    global _vf, _vfc
    _vf           = cStringIO.StringIO()
    _vfc          = cStringIO.StringIO()

# -----------------------------------------------------------------------------
# class Production:
#
# This class stores the raw information about a single production or grammar rule.
# It has a few required attributes:
#
#       name     - Name of the production (nonterminal)
#       prod     - A list of symbols making up its production
#       number   - Production number.
#
# In addition, a few additional attributes are used to help with debugging or
# optimization of table generation.
#
#       file     - File where production action is defined.
#       lineno   - Line number where action is defined
#       func     - Action function
#       prec     - Precedence level
#       lr_next  - Next LR item. Example, if we are ' E -> E . PLUS E'
#                  then lr_next refers to 'E -> E PLUS . E'   
#       lr_index - LR item index (location of the ".") in the prod list.
#       len      - Length of the production (number of symbols on right hand side)
# -----------------------------------------------------------------------------

class Production:
    def __init__(self,**kw):
        for k,v in kw.items():
            setattr(self,k,v)
        self.lr_index = -1
        self.lr0_added = 0    # Flag indicating whether or not added to LR0 closure
        self.usyms = [ ]
        
    def __str__(self):
        if self.prod:
            s = "%s -> %s" % (self.name," ".join(self.prod))
        else:
            s = "%s -> <empty>" % self.name
        return s

    def __repr__(self):
        return str(self)

    # Compute lr_items from the production
    def lr_item(self,n):
        if n > len(self.prod): return None
        p = Production()
        p.name = self.name
        p.prod = list(self.prod)
        p.number = self.number
        p.lr_index = n
        p.prod.insert(n,".")
        p.prod = tuple(p.prod)
        p.len = len(p.prod)
        p.usyms = self.usyms

        # Precompute list of productions immediately following
        try:
            p.lrafter = Prodnames[p.prod[n+1]]
        except (IndexError,KeyError),e:
            p.lrafter = []
        try:
            p.lrbefore = p.prod[n-1]
        except IndexError:
            p.lrbefore = None

        return p
            

# Utility function
def is_identifier(s):
    for c in s:
        if not (c.isalnum() or c == '_'): return 0
    return 1

# -----------------------------------------------------------------------------
# add_production()
#
# Given an action function, this function assembles a production rule.
# The production rule is assumed to be found in the function's docstring.
# This rule has the general syntax:
#
#              name1 ::= production1
#                     |  production2
#                     |  production3
#                    ...
#                     |  productionn
#              name2 ::= production1
#                     |  production2
#                    ... 
# -----------------------------------------------------------------------------

def add_production(f,file,line,prodname,syms):
    
    if Terminals.has_key(prodname):
        print "%s:%d. Illegal rule name '%s'. Already defined as a token." % (file,line,prodname)
        return -1
    if prodname == 'error':
        print "%s:%d. Illegal rule name '%s'. error is a reserved word." % (file,line,prodname)
        return -1
                
    if not is_identifier(prodname):
        print "%s:%d. Illegal rule name '%s'" % (file,line,prodname)
        return -1

    for s in syms:
        if not is_identifier(s) and s != '%prec':
            print "%s:%d. Illegal name '%s' in rule '%s'" % (file,line,s, prodname)
            return -1

    # See if the rule is already in the rulemap
    map = "%s -> %s" % (prodname,syms)
    if Prodmap.has_key(map):
        m = Prodmap[map]
        print "%s:%d. Duplicate rule %s." % (file,line, m)
        print "%s:%d. Previous definition at %s:%d" % (file,line, m.file, m.line)
        return -1

    p = Production()
    p.name = prodname
    p.prod = syms
    p.file = file
    p.line = line
    p.func = f
    p.number = len(Productions)

            
    Productions.append(p)
    Prodmap[map] = p
    if not Nonterminals.has_key(prodname):
        Nonterminals[prodname] = [ ]
    
    # Add all terminals to Terminals
    i = 0
    while i < len(p.prod):
        t = p.prod[i]
        if t == '%prec':
            try:
                precname = p.prod[i+1]
            except IndexError:
                print "%s:%d. Syntax error. Nothing follows %%prec." % (p.file,p.line)
                return -1

            prec = Precedence.get(precname,None)
            if not prec:
                print "%s:%d. Nothing known about the precedence of '%s'" % (p.file,p.line,precname)
                return -1
            else:
                p.prec = prec
            del p.prod[i]
            del p.prod[i]
            continue

        if Terminals.has_key(t):
            Terminals[t].append(p.number)
            # Is a terminal.  We'll assign a precedence to p based on this
            if not hasattr(p,"prec"):
                p.prec = Precedence.get(t,('right',0))
        else:
            if not Nonterminals.has_key(t):
                Nonterminals[t] = [ ]
            Nonterminals[t].append(p.number)
        i += 1

    if not hasattr(p,"prec"):
        p.prec = ('right',0)
        
    # Set final length of productions
    p.len  = len(p.prod)
    p.prod = tuple(p.prod)

    # Calculate unique syms in the production
    p.usyms = [ ]
    for s in p.prod:
        if s not in p.usyms:
            p.usyms.append(s)
    
    # Add to the global productions list
    try:
        Prodnames[p.name].append(p)
    except KeyError:
        Prodnames[p.name] = [ p ]
    return 0

# Given a raw rule function, this function rips out its doc string
# and adds rules to the grammar

def add_function(f):
    line = f.func_code.co_firstlineno
    file = f.func_code.co_filename
    error = 0
    
    if f.func_code.co_argcount > 1:
        print "%s:%d. Rule '%s' has too many arguments." % (file,line,f.__name__)
        return -1

    if f.func_code.co_argcount < 1:
        print "%s:%d. Rule '%s' requires an argument." % (file,line,f.__name__)
        return -1
          
    if f.__doc__:
        # Split the doc string into lines
        pstrings = f.__doc__.splitlines()
        lastp = None
        dline = line
        for ps in pstrings:
            dline += 1
            p = ps.split()
            if not p: continue
            try:
                if p[0] == '|':
                    # This is a continuation of a previous rule
                    if not lastp:
                        print "%s:%d. Misplaced '|'." % (file,dline)
                        return -1
                    prodname = lastp
                    if len(p) > 1:
                        syms = p[1:]
                    else:
                        syms = [ ]
                else:
                    prodname = p[0]
                    lastp = prodname
                    assign = p[1]
                    if len(p) > 2:
                        syms = p[2:]
                    else:
                        syms = [ ]
                    if assign != ':' and assign != '::=':
                        print "%s:%d. Syntax error. Expected ':'" % (file,dline)
                        return -1
                e = add_production(f,file,dline,prodname,syms)
                error += e
            except StandardError:
                print "%s:%d. Syntax error in rule '%s'" % (file,dline,ps)
                error -= 1
    else:
        print "%s:%d. No documentation string specified in function '%s'" % (file,line,f.__name__)
    return error

# -----------------------------------------------------------------------------
# check_cycles()
#
# This function looks at the various parsing rules and tries to detect
# infinite recursion cycles (grammar rules where there is no possible way
# to derive a string of terminals).
# -----------------------------------------------------------------------------

def check_cycles(p=None,val=1,start=None):
    if not p:
        # Walk through list of productions and zero out cycle counts
        for i in Productions:
            i.cychk = 0            # Already encountered this rule
            i.cyvalue = -1
        error = 0

        # First run a cycle check on the top rule.  This will find
        # everything that's used.

        p = Productions[1]
        p = Productions[0]        
        c = check_cycles(p,1)
        val = 2
        for n,pl in Prodnames.items():
            term = 0
            used = 0
            for p in pl:
                if not p.cychk:
                    continue
                used +=1
                term += check_cycles(p,val)
            if not used:
                print "yacc: Rule '%s' never used." % n
                
            if used and not term and Nonterminals[n]:
                print "yacc: Infinite recursion detected in rule '%s'." % n
                error = 1
            val += 1
        return error

    # We are checking this rule for a cycle
    if p.cychk == val:
        # Hmmm. We already saw this rule before.
        if p.cyvalue >= 0:
            return p.cyvalue
        else:
            return 0

    p.cyvalue = -1
    # Looking for cycles
    p.cychk = val

    # Look at all of the symbols to the right of this production
    term = 0
    for s in p.prod:
        # Get list of productions for 's'
        pl = Prodnames.get(s,None)
        if not pl:
            term += 1
            continue           # Must be a terminal. Continue
        
        # Check all of the rules for each non-terminal for cycles
        pterm = 0
        for x in pl:
            c = check_cycles(x,val)
            if c:
                pterm = 1
                if val > 1: break
        term += pterm

    # All right hand side symbols terminate
    # print p.name, term, len(p.prod), val
    if term == len(p.prod):
        p.cyvalue = 1
    else:
        p.cyvalue = 0
        
    return p.cyvalue

# -----------------------------------------------------------------------------
# verify_productions()
#
# This function examines all of the supplied rules to see if they seem valid.
# -----------------------------------------------------------------------------
def verify_productions(cycle_check=1):
    error = 0
    for p in Productions:
        if not p: continue

        # Look for a purely empty productions and record in special dictionary
        if not len(p.prod):
            Prodempty[p.name] = p
            continue
        
        for s in p.prod:
            if not Prodnames.has_key(s) and not Terminals.has_key(s) and s != 'error':
                print "%s:%d. Symbol '%s' used, but not defined as a token or a rule." % (p.file,p.line,s)
                error = 1
                continue

    unused_tok = 0 
    # Now verify all of the tokens
    if yaccdebug:
        _vf.write("Unused terminals:\n\n")
    for s,v in Terminals.items():
        if s != 'error' and not v:
            print "yacc: Warning. Token '%s' defined, but not used." % s
            if yaccdebug: _vf.write("   %s\n"% s)
            unused_tok += 1

    # Print out all of the productions
    if yaccdebug:
        _vf.write("\nGrammar\n\n")
        for i in range(1,len(Productions)):
            _vf.write("Rule %-5d %s\n" % (i, Productions[i]))
        
    unused_prod = 0
    # Verify the use of all productions
    for s,v in Nonterminals.items():
        if not v:
            p = Prodnames[s][0]
            print "%s:%d: Warning. Rule '%s' defined, but not used." % (p.file,p.line, s)
            unused_prod += 1

    
    if unused_tok == 1:
        print "yacc: Warning. There is 1 unused token."
    if unused_tok > 1:
        print "yacc: Warning. There are %d unused tokens." % unused_tok

    if unused_prod == 1:
        print "yacc: Warning. There is 1 unused rule."
    if unused_prod > 1:
        print "yacc: Warning. There are %d unused rules." % unused_prod

    if yaccdebug:
        _vf.write("\nTerminals, with rules where they appear\n\n")
        for k in Terminals.keys():
            _vf.write("%-20s : %s\n" % (k, " ".join([str(s) for s in Terminals[k]])))
        _vf.write("\nNonterminals, with rules where they appear\n\n")
        for k in Nonterminals.keys():
            _vf.write("%-20s : %s\n" % (k, " ".join([str(s) for s in Nonterminals[k]])))

    if (cycle_check):
        error += check_cycles()
    return error

# -----------------------------------------------------------------------------
# build_lritems()
#
# This function walks the list of productions and builds a complete set of the
# LR items.  The LR items are stored in two ways:  First, they are uniquely
# numbered and placed in the list _lritems.  Second, a linked list of LR items
# is built for each production.  For example:
#
#   E -> E PLUS E
#
# Creates the list
#
#  [E -> . E PLUS E, E -> E . PLUS E, E -> E PLUS . E, E -> E PLUS E . ] 
# -----------------------------------------------------------------------------

def build_lritems():
    for p in Productions:
        lastlri = p
        lri = p.lr_item(0)
        i = 0
        while 1:
            lri = p.lr_item(i)
            lastlri.lr_next = lri
            if not lri: break
            lri.lr_num = len(LRitems)
            LRitems.append(lri)
            lastlri = lri
            i += 1

    # In order for the rest of the parser generator to work, we need to
    # guarantee that no more lritems are generated.  Therefore, we nuke
    # the p.lr_item method.  (Only used in debugging)
    # Production.lr_item = None

# -----------------------------------------------------------------------------
# add_precedence()
#
# Given a list of precedence rules, add to the precedence table.
# -----------------------------------------------------------------------------

def add_precedence(plist):
    plevel = 0
    error = 0
    for p in plist:
        plevel += 1
        try:
            prec = p[0]
            terms = p[1:]
            if prec != 'left' and prec != 'right':
                print "yacc: Invalid precedence '%s'" % prec
                return -1
            for t in terms:
                if Precedence.has_key(t):
                    print "yacc: Precedence already specified for terminal '%s'" % t
                    error += 1
                    continue
                Precedence[t] = (prec,plevel)
        except:
            print "yacc: Invalid precedence table."
            error += 1

    return error

# -----------------------------------------------------------------------------
# augment_grammar()
#
# Compute the augmented grammar.  This is just a rule S' -> start where start
# is the starting symbol.
# -----------------------------------------------------------------------------

def augment_grammar(start=None):
    if not start:
        start = Productions[1].name
    Productions[0] = Production(name="S'",prod=[start],number=0,len=1,prec=('right',0),func=None)
    Productions[0].usyms = [ start ]
    Nonterminals[start].append(0)
    
# -----------------------------------------------------------------------------
# first()
#
# Compute the value of FIRST1(X) where x is a terminal, nonterminal, or tuple
# of grammar symbols.
# -----------------------------------------------------------------------------
def first(x):
    # Check if already computed
    fst = First.get(x,None)
    if fst: return fst
    
    if isinstance(x,types.TupleType):
        # We are computing First(x1,x2,x3,x4,...xn)
        fst = [ ]
        numempty = 0
        for s in x:
            f = first(s)
            for i in f:
                if i == '<empty>':
                    numempty +=1
                    continue
                if i not in fst: fst.append(i)
            if not numempty: break
        if numempty == len(x):
            fst.append('<empty>')

    elif Terminals.has_key(x):
        fst = [x]

    elif Prodnames.has_key(x):
        fst = [ ]
        prodlist = Prodnames[x]
        for p in prodlist:
            # Check if we're already computing first on this production
            if p.cfirst: continue
        
            # Check for empty, we just add empty to first in this case
            if not len(p.prod):
                fst.append('<empty>')
                p.cfirst = 1
                continue

            # Go down the list of production symbols looking for empty
            # productions

            p.cfirst = 1
            for ps in p.prod:
                if ps == '<empty>': continue
                # Add everything in first(ps) to our set

                f = first(ps)
                for i in f:
                    if i not in fst: fst.append(i)
                # If this rule doesn't produce empty, we're done
                if not Prodempty.has_key(ps):
                    break
    else:
        raise YaccError, "first: %s not a terminal or nonterminal" % x

    First[x] = fst
    return fst

# FOLLOW(x)
# Given a non-terminal.  This function computes the set of all symbols
# that might follow it.  Dragon book, p. 189.

def compute_follow(start=None):
    # Add '$' to the follow list of the start symbol
    for k in Nonterminals.keys():
        Follow[k] = [ ]

    if not start:
        start = Productions[1].name
        
    Follow[start] = [ '$' ]
        
    while 1:
        didadd = 0
        for p in Productions[1:]:
            # Here is the production set
            for i in range(len(p.prod)):
                B = p.prod[i]
                if Nonterminals.has_key(B):
                    # Okay. We got a non-terminal in a production
                    fst = first(p.prod[i+1:])
                    hasempty = 0
                    for f in fst:
                        if f != '<empty>' and f not in Follow[B]:
                            Follow[B].append(f)
                            didadd = 1
                        if f == '<empty>':
                            hasempty = 1
                    if hasempty or i == (len(p.prod)-1):
                        # Add elements of follow(a) to follow(b)
                        for f in Follow[p.name]:
                            if f not in Follow[B]:
                                Follow[B].append(f)
                                didadd = 1
        if not didadd: break

# Compute first for all symbols
def compute_first1():

    # Result first flag
    for p in Productions:
        p.cfirst = 0
        
    # Compute all terminals
    for t in Terminals.keys():
        first(t)

    # Compute for all nonterminals
    for n in Nonterminals.keys():
        prodlist = Prodnames[n]
        first(n)

    # First for the end symbol marker
    First['$'] = ['$']
    First['#'] = ['#']

# -----------------------------------------------------------------------------
#                           === SLR Generation ===
#
# The following functions are used to construct SLR (Simple LR) parsing tables
# as described on p.221-229 of the dragon book.
# -----------------------------------------------------------------------------

# Global variables for the LR parsing engine
def lr_init_vars():
    global _lr_action, _lr_goto, _lr_method
    global _lr_goto_cache
    
    _lr_action       = { }        # Action table
    _lr_goto         = { }        # Goto table
    _lr_method       = "Unknown"  # LR method used
    _lr_goto_cache   = { }

# Compute the LR(0) closure operation on I, where I is a set of LR(0) items.
# prodlist is a list of productions.

_add_count = 0       # Counter used to detect cycles

def lr0_closure(I):
    global _add_count
    
    _add_count += 1
    prodlist = Productions
    
    # Add everything in I to J        
    J = I[:]
    didadd = 1
    while didadd:
        didadd = 0
        for j in J:
            for x in j.lrafter:
                if x.lr0_added == _add_count: continue
                # Add B --> .G to J
                J.append(x.lr_next)
                x.lr0_added = _add_count
                didadd = 1
               
    return J

# Compute the LR(0) goto function goto(I,X) where I is a set
# of LR(0) items and X is a grammar symbol.   This function is written
# in a way that guarantees uniqueness of the generated goto sets
# (i.e. the same goto set will never be returned as two different Python
# objects).  With uniqueness, we can later do fast set comparisons using
# id(obj) instead of element-wise comparison.

def lr0_goto(I,x):
    # First we look for a previously cached entry
    g = _lr_goto_cache.get((id(I),x),None)
    if g: return g

    # Now we generate the goto set in a way that guarantees uniqueness
    # of the result
    
    s = _lr_goto_cache.get(x,None)
    if not s:
        s = { }
        _lr_goto_cache[x] = s

    gs = [ ]
    for p in I:
        n = p.lr_next
        if n and n.lrbefore == x:
            s1 = s.get(id(n),None)
            if not s1:
                s1 = { }
                s[id(n)] = s1
            gs.append(n)
            s = s1
    g = s.get('$',None)
    if not g:
        if gs:
            g = lr0_closure(gs)
            s['$'] = g
        else:
            s['$'] = gs
    _lr_goto_cache[(id(I),x)] = g
    return g

# Compute the kernel of a set of LR(0) items
def lr0_kernel(I):
    KI = [ ]
    for p in I:
        if p.name == "S'" or p.lr_index > 0 or p.len == 0:
            KI.append(p)

    return KI

_lr0_cidhash = { }

# Compute the LR(0) sets of item function
def lr0_items():
    
    C = [ lr0_closure([Productions[0].lr_next]) ]
    i = 0
    for I in C:
        _lr0_cidhash[id(I)] = i
        i += 1

    # Loop over the items in C and each grammar symbols
    i = 0
    while i < len(C):
        I = C[i]
        i += 1

        # Collect all of the symbols that could possibly be in the goto(I,X) sets
        asyms = { }
        for ii in I:
            for s in ii.usyms:
                asyms[s] = None

        for x in asyms.keys():
            g = lr0_goto(I,x)
            if not g:  continue
            if _lr0_cidhash.has_key(id(g)): continue
            _lr0_cidhash[id(g)] = len(C)            
            C.append(g)
            
    return C

# -----------------------------------------------------------------------------
# slr_parse_table()
#
# This function constructs an SLR table.
# -----------------------------------------------------------------------------
def slr_parse_table():
    global _lr_method
    goto = _lr_goto           # Goto array
    action = _lr_action       # Action array
    actionp = { }             # Action production array (temporary)

    _lr_method = "SLR"
    
    n_srconflict = 0
    n_rrconflict = 0

    if yaccdebug:
        print "yacc: Generating SLR parsing table..."
    if yaccdebug:
        _vf.write("\n\nParsing method: SLR\n\n")
        
    # Step 1: Construct C = { I0, I1, ... IN}, collection of LR(0) items
    # This determines the number of states
    
    C = lr0_items()

    # Build the parser table, state by state
    st = 0
    for I in C:
        # Loop over each production in I
        actlist = [ ]              # List of actions
        
        if yaccdebug:
            _vf.write("\nstate %d\n\n" % st)
            for p in I:
                _vf.write("    %s\n" % str(p))
            _vf.write("\n")

        for p in I:
            try:
                if p.prod[-1] == ".":
                    if p.name == "S'":
                        # Start symbol. Accept!
                        action[st,"$"] = 0
                        actionp[st,"$"] = p
                    else:
                        # We are at the end of a production.  Reduce!
                        for a in Follow[p.name]:
                            actlist.append((a,p,"reduce using rule %d" % p.number))
                            r = action.get((st,a),None)
                            if r is not None:
                                # Whoa. Have a shift/reduce or reduce/reduce conflict
                                if r > 0:
                                    # Need to decide on shift or reduce here
                                    # By default we favor shifting. Need to add
                                    # some precedence rules here.
                                    sprec,slevel = Productions[actionp[st,a].number].prec                                    
                                    rprec,rlevel = Precedence.get(a,('right',0))
                                    if (slevel < rlevel) or ((slevel == rlevel) and (rprec == 'left')):
                                        # We really need to reduce here.  
                                        action[st,a] = -p.number
                                        actionp[st,a] = p
                                        if not slevel and not rlevel:
                                            _vfc.write("shift/reduce conflict in state %d resolved as reduce.\n" % st)
                                            _vf.write("  ! shift/reduce conflict for %s resolved as reduce.\n" % a)
                                            n_srconflict += 1
                                    else:
                                        # Hmmm. Guess we'll keep the shift
                                        if not slevel and not rlevel:
                                            _vfc.write("shift/reduce conflict in state %d resolved as shift.\n" % st)
                                            _vf.write("  ! shift/reduce conflict for %s resolved as shift.\n" % a)
                                            n_srconflict +=1                                    
                                elif r < 0:
                                    # Reduce/reduce conflict.   In this case, we favor the rule
                                    # that was defined first in the grammar file
                                    oldp = Productions[-r]
                                    pp = Productions[p.number]
                                    if oldp.line > pp.line:
                                        action[st,a] = -p.number
                                        actionp[st,a] = p
                                    # print "Reduce/reduce conflict in state %d" % st
                                    n_rrconflict += 1
                                    _vfc.write("reduce/reduce conflict in state %d resolved using rule %d.\n" % (st, actionp[st,a].number))
                                    _vf.write("  ! reduce/reduce conflict for %s resolved using rule %d.\n" % (a,actionp[st,a].number))
                                else:
                                    print "Unknown conflict in state %d" % st
                            else:
                                action[st,a] = -p.number
                                actionp[st,a] = p
                else:
                    i = p.lr_index
                    a = p.prod[i+1]       # Get symbol right after the "."
                    if Terminals.has_key(a):
                        g = lr0_goto(I,a)
                        j = _lr0_cidhash.get(id(g),-1)
                        if j >= 0:
                            # We are in a shift state
                            actlist.append((a,p,"shift and go to state %d" % j))
                            r = action.get((st,a),None)
                            if r is not None:
                                # Whoa have a shift/reduce or shift/shift conflict
                                if r > 0:
                                    if r != j:
                                        print "Shift/shift conflict in state %d" % st
                                elif r < 0:
                                    # Do a precedence check.
                                    #   -  if precedence of reduce rule is higher, we reduce.
                                    #   -  if precedence of reduce is same and left assoc, we reduce.
                                    #   -  otherwise we shift
                                    rprec,rlevel = Productions[actionp[st,a].number].prec
                                    sprec,slevel = Precedence.get(a,('right',0))
                                    if (slevel > rlevel) or ((slevel == rlevel) and (rprec != 'left')):
                                        # We decide to shift here... highest precedence to shift
                                        action[st,a] = j
                                        actionp[st,a] = p
                                        if not slevel and not rlevel:
                                            n_srconflict += 1
                                            _vfc.write("shift/reduce conflict in state %d resolved as shift.\n" % st)
                                            _vf.write("  ! shift/reduce conflict for %s resolved as shift.\n" % a)
                                    else:                                            
                                        # Hmmm. Guess we'll keep the reduce
                                        if not slevel and not rlevel:
                                            n_srconflict +=1
                                            _vfc.write("shift/reduce conflict in state %d resolved as reduce.\n" % st)
                                            _vf.write("  ! shift/reduce conflict for %s resolved as reduce.\n" % a)
                                            
                                else:
                                    print "Unknown conflict in state %d" % st
                            else:
                                action[st,a] = j
                                actionp[st,a] = p
                                
            except StandardError,e:
                raise YaccError, "Hosed in slr_parse_table", e

        # Print the actions associated with each terminal
        if yaccdebug:
          for a,p,m in actlist:
            if action.has_key((st,a)):
                if p is actionp[st,a]:
                    _vf.write("    %-15s %s\n" % (a,m))
          _vf.write("\n")
          for a,p,m in actlist:
            if action.has_key((st,a)):
                if p is not actionp[st,a]:
                    _vf.write("  ! %-15s [ %s ]\n" % (a,m))
            
        # Construct the goto table for this state
        nkeys = { }
        for ii in I:
            for s in ii.usyms:
                if Nonterminals.has_key(s):
                    nkeys[s] = None

        # Construct the goto table for this state
        for n in nkeys.keys():
            g = lr0_goto(I,n)
            j = _lr0_cidhash.get(id(g),-1)            
            if j >= 0:
                goto[st,n] = j

        st += 1

    if n_srconflict == 1:
        print "yacc: %d shift/reduce conflict" % n_srconflict
    if n_srconflict > 1:
        print "yacc: %d shift/reduce conflicts" % n_srconflict        
    if n_rrconflict == 1:
        print "yacc: %d reduce/reduce conflict" % n_rrconflict
    if n_rrconflict > 1:
        print "yacc: %d reduce/reduce conflicts" % n_rrconflict


# -----------------------------------------------------------------------------
#                       ==== LALR(1) Parsing ====
# **** UNFINISHED!  6/16/01
# -----------------------------------------------------------------------------


# Compute the lr1_closure of a set I.  I is a list of tuples (p,a) where
# p is a LR0 item and a is a terminal

_lr1_add_count = 0

def lr1_closure(I):
    global _lr1_add_count

    _lr1_add_count += 1

    J = I[:]

    # Loop over items (p,a) in I.
    ji = 0
    while ji < len(J):
        p,a = J[ji]
        #  p = [ A -> alpha . B beta]

        #  For each production B -> gamma 
        for B in p.lr1_after:
            f = tuple(p.lr1_beta + (a,))

            # For each terminal b in first(Beta a)
            for b in first(f):
                # Check if (B -> . gamma, b) is in J
                # Only way this can happen is if the add count mismatches
                pn = B.lr_next
                if pn.lr_added.get(b,0) == _lr1_add_count: continue
                pn.lr_added[b] = _lr1_add_count
                J.append((pn,b))
        ji += 1

    return J

def lalr_parse_table():

    # Compute some lr1 information about all of the productions
    for p in LRitems:
        try:
            after = p.prod[p.lr_index + 1]
            p.lr1_after = Prodnames[after]
            p.lr1_beta = p.prod[p.lr_index + 2:]
        except LookupError:
            p.lr1_after = [ ]
            p.lr1_beta = [ ]
        p.lr_added = { }

    # Compute the LR(0) items
    C = lr0_items()
    CK = []
    for I in C:
        CK.append(lr0_kernel(I))

    print CK
    
# -----------------------------------------------------------------------------
#                          ==== LR Utility functions ====
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# _lr_write_tables()
#
# This function writes the LR parsing tables to a file
# -----------------------------------------------------------------------------

def lr_write_tables(modulename=tab_module):
    filename = modulename + ".py"
    try:
        f = open(filename,"w")

        f.write("""
# %s
# This file is automatically generated. Do not edit.

_lr_method = %s

_lr_signature = %s
""" % (filename, repr(_lr_method), repr(Signature.digest())))

        # Change smaller to 0 to go back to original tables
        smaller = 1
                
        # Factor out names to try and make smaller
        if smaller:
            items = { }
        
            for k,v in _lr_action.items():
                i = items.get(k[1])
                if not i:
                    i = ([],[])
                    items[k[1]] = i
                i[0].append(k[0])
                i[1].append(v)

            f.write("\n_lr_action_items = {")
            for k,v in items.items():
                f.write("%r:([" % k)
                for i in v[0]:
                    f.write("%r," % i)
                f.write("],[")
                for i in v[1]:
                    f.write("%r," % i)
                           
                f.write("]),")
            f.write("}\n")

            f.write("""
_lr_action = { }
for _k, _v in _lr_action_items.items():
   for _x,_y in zip(_v[0],_v[1]):
       _lr_action[(_x,_k)] = _y
del _lr_action_items
""")
            
        else:
            f.write("\n_lr_action = { ");
            for k,v in _lr_action.items():
                f.write("(%r,%r):%r," % (k[0],k[1],v))
            f.write("}\n");

        if smaller:
            # Factor out names to try and make smaller
            items = { }
        
            for k,v in _lr_goto.items():
                i = items.get(k[1])
                if not i:
                    i = ([],[])
                    items[k[1]] = i
                i[0].append(k[0])
                i[1].append(v)

            f.write("\n_lr_goto_items = {")
            for k,v in items.items():
                f.write("%r:([" % k)
                for i in v[0]:
                    f.write("%r," % i)
                f.write("],[")
                for i in v[1]:
                    f.write("%r," % i)
                           
                f.write("]),")
            f.write("}\n")

            f.write("""
_lr_goto = { }
for _k, _v in _lr_goto_items.items():
   for _x,_y in zip(_v[0],_v[1]):
       _lr_goto[(_x,_k)] = _y
del _lr_goto_items
""")
        else:
            f.write("\n_lr_goto = { ");
            for k,v in _lr_goto.items():
                f.write("(%r,%r):%r," % (k[0],k[1],v))                    
            f.write("}\n");
        f.close()

    except IOError,e:
        print "Unable to create '%s'" % filename
        print e
        return

def lr_read_tables(module=tab_module):
    global _lr_action, _lr_goto
    try:
        exec "import %s as parsetab" % module
        
        if string.find(sys.platform,"java")>-1 \
           or Signature.digest() == parsetab._lr_signature:
            _lr_action = parsetab._lr_action
            _lr_goto   = parsetab._lr_goto
            return 1
        else:
            return 0
        
    except (ImportError,AttributeError):
        return 0

# -----------------------------------------------------------------------------
# yacc(module)
#
# Build the parser module
# -----------------------------------------------------------------------------

def yacc(method=default_lr, debug=yaccdebug, module=None, tabmodule=tab_module, start=None, check_recursion=1):
    global yaccdebug
    yaccdebug = debug
    
    initialize_vars()
    files = { }
    error = 0

    # Add starting symbol to signature
    if start:
        Signature.update(start)
        
    # Try to figure out what module we are working with
    if module:
        # User supplied a module object.
        if not isinstance(module, types.ModuleType):
            raise ValueError,"Expected a module"

        ldict = module.__dict__
        
    else:
        # No module given.  We might be able to get information from the caller.
        # Throw an exception and unwind the traceback to get the globals
        
        try:
            raise RuntimeError
        except RuntimeError:
            e,b,t = sys.exc_info()
            f = t.tb_frame
            f = f.f_back           # Walk out to our calling function
            ldict = f.f_globals    # Grab its globals dictionary
        
    # Get the tokens map
    tokens = ldict.get("tokens",None)
    
    if not tokens:
        raise YaccError,"module does not define a list 'tokens'"
    if not (isinstance(tokens,types.ListType) or isinstance(tokens,types.TupleType)):
        raise YaccError,"tokens must be a list or tuple."

    # Check to see if a requires dictionary is defined.
    requires = ldict.get("require",None)
    if requires:
        if not (isinstance(requires,types.DictType)):
            raise YaccError,"require must be a dictionary."

        for r,v in requires.items():
            try:
                if not (isinstance(v,types.ListType)):
                    raise TypeError
                v1 = [x.split(".") for x in v]
                Requires[r] = v1
            except StandardError:
                print "Invalid specification for rule '%s' in require. Expected a list of strings" % r            

        
    # Build the dictionary of terminals.  We a record a 0 in the
    # dictionary to track whether or not a terminal is actually
    # used in the grammar

    if 'error' in tokens:
        print "yacc: Illegal token 'error'.  Is a reserved word."
        raise YaccError,"Illegal token name"

    for n in tokens:
        if Terminals.has_key(n):
            print "yacc: Warning. Token '%s' multiply defined." % n
        Terminals[n] = [ ]

    Terminals['error'] = [ ]

    # Get the precedence map (if any)
    prec = ldict.get("precedence",None)
    if prec:
        if not (isinstance(prec,types.ListType) or isinstance(prec,types.TupleType)):
            raise YaccError,"precedence must be a list or tuple."
        add_precedence(prec)
        Signature.update(repr(prec))

    for n in tokens:
        if not Precedence.has_key(n):
            Precedence[n] = ('right',0)         # Default, right associative, 0 precedence

    # Look for error handler
    ef = ldict.get('p_error',None)
    if ef:
        if not isinstance(ef,types.FunctionType):
            raise YaccError,"'p_error' defined, but is not a function."
        eline = ef.func_code.co_firstlineno
        efile = ef.func_code.co_filename
        files[efile] = None
        
        if (ef.func_code.co_argcount != 1):
            raise YaccError,"%s:%d. p_error() requires 1 argument." % (efile,eline)
        global Errorfunc
        Errorfunc = ef
    else:
        print "yacc: Warning. no p_error() function is defined."
        
    # Get the list of built-in functions with p_ prefix
    symbols = [ldict[f] for f in ldict.keys()
               if (isinstance(ldict[f],types.FunctionType) and ldict[f].__name__[:2] == 'p_'
                   and ldict[f].__name__ != 'p_error')]

    # Check for non-empty symbols
    if len(symbols) == 0:
        raise YaccError,"no rules of the form p_rulename are defined."
    
    # Sort the symbols by line number
    symbols.sort(lambda x,y: cmp(x.func_code.co_firstlineno,y.func_code.co_firstlineno))

    # Add all of the symbols to the grammar
    for f in symbols:
        if (add_function(f)) < 0:
            error += 1
        else:
            files[f.func_code.co_filename] = None

    # Make a signature of the docstrings
    for f in symbols:
        if f.__doc__:
            Signature.update(f.__doc__)
    
    lr_init_vars()

    if error:
        raise YaccError,"Unable to construct parser."

    if not lr_read_tables(tabmodule):
        sys.stderr.write("lr_read_tables failed; re-building\n") # ssb

        # Validate files
        for filename in files.keys():
            if not validate_file(filename):
                error = 1

        # Validate dictionary
        validate_dict(ldict)

        if start and not Prodnames.has_key(start):
            raise YaccError,"Bad starting symbol '%s'" % start
        
        augment_grammar(start)    
        error = verify_productions(cycle_check=check_recursion)
        otherfunc = [ldict[f] for f in ldict.keys()
               if (isinstance(ldict[f],types.FunctionType) and ldict[f].__name__[:2] != 'p_')]

        if error:
            raise YaccError,"Unable to construct parser."
            
        build_lritems()
        compute_first1()
        compute_follow(start)
        
        if method == 'SLR':
            slr_parse_table()
        elif method == 'LALR1':
            lalr_parse_table()
            return
        else:
            raise YaccError, "Unknown parsing method '%s'" % method
            
        lr_write_tables(tabmodule)        
    
        if yaccdebug:
            try:
                f = open(debug_file,"w")
                f.write(_vfc.getvalue())
                f.write("\n\n")
                f.write(_vf.getvalue())
                f.close()
            except IOError,e:
                print "yacc: can't create '%s'" % debug_file,e
        
    # Made it here.   Create a parser object and set up its internal state.
    # Set global parse() method to bound method of parser object.

    p = Parser("xyzzy")
    p.productions = Productions
    p.errorfunc = Errorfunc
    p.action = _lr_action
    p.goto   = _lr_goto
    p.method = _lr_method
    p.require = Requires

    global parse
    parse = p.parse

    # Clean up all of the globals we created
    yacc_cleanup()
    return p

# yacc_cleanup function.  Delete all of the global variables
# used during table construction

def yacc_cleanup():
    global _lr_action, _lr_goto, _lr_method, _lr_goto_cache
    del _lr_action, _lr_goto, _lr_method, _lr_goto_cache

    global Productions, Prodnames, Prodmap, Prodempty, Terminals 
    global Nonterminals, First, Follow, Precedence, LRitems
    global Errorfunc, Signature, Requires

    del Productions, Prodnames, Prodmap, Prodempty, Terminals
    del Nonterminals, First, Follow, Precedence, LRitems
    del Errorfunc, Signature, Requires

    global _vf, _vfc
    del _vf, _vfc
    
    
# Stub that raises an error if parsing is attempted without first calling yacc()
def parse(*args,**kwargs):
    raise YaccError, "yacc: No parser built with yacc()"

