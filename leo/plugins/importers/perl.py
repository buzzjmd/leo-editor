#@+leo-ver=5-thin
#@+node:ekr.20161027100313.1: * @file importers/perl.py
'''The @auto importer for Perl.'''
import leo.plugins.importers.basescanner as basescanner
import leo.core.leoGlobals as g
import re
ScanState = basescanner.ScanState
StateScanner = basescanner.StateScanner
gen_v2 = g.gen_v2
#@+others
#@+node:ekr.20161027094537.5: ** class PerlStateScanner
class PerlStateScanner(StateScanner):
    '''A class to store and update scanning state.'''
    def __init__(self, c):
        '''Ctor for the PerlStateScanner class.'''
        StateScanner.__init__(self, c)
            # Init the base class.
        self.base_curlies = self.curlies = 0
        self.base_parens = self.parens = 0
        self.context = '' # Represents cross-line constructs.
        self.stack = []

    #@+others
    #@+node:ekr.20161104150450.1: *3* perl_state.__repr__
    def __repr__(self):
        '''PerlStateScanner.__repr__'''
        return 'PerlStateScanner: base: %3r now: %3r context: %2r' % (
            '{' * self.base_curlies + '(' * self.base_parens, 
            '{' * self.curlies + '(' * self.parens,
            self.context)

    __str__ = __repr__
    #@+node:ekr.20161104084712.5: *3* perl_state.clear (to be removed)
    def clear(self):
        '''Clear the state.'''
        self.base_curlies = self.curlies = 0
        self.base_parens = self.parens = 0
        self.context = ''
    #@+node:ekr.20161104150004.1: *3* perl_state.initial_state
    def initial_state(self):
        '''Return the initial counts.'''
        # return '', 0, 0
        return ScanState(
            context = '',
            curlies = 0,
            parens = 0,
            tag = 'Perl',
        )
    #@+node:ekr.20161027094537.11: *3* perl_state.scan_line
    def scan_line(self, s):
        '''Update the scan state by scanning s.'''
        # pylint: disable=arguments-differ
        trace = False and not g.unitTesting
        match = self.match
        i = 0
        while i < len(s):
            progress = i
            ch = s[i]
            if self.context:
                assert self.context in ('"', "'", "="), repr(self.context)
                if ch == '\\':
                    i += 1
                elif i == 0 and self.context == '=' and match(s, i, '=cut'):
                    self.context = '' # End the perlpod string.
                    i += 4
                elif self.context == ch:
                    self.context = '' # End the string.
                else:
                    pass # Eat the string character later.
            elif ch == '#':
                break # The single-line comment ends the line.
            elif ch in ('"', "'"):
                self.context = ch
            elif ch == '{': self.curlies += 1
            elif ch == '}': self.curlies -= 1
            elif ch == '(': self.parens += 1
            elif ch == ')': self.parens -= 1
            elif i == 0 and ch == '=':
                self.context = '=' # perlpod string.
            else:
                for pattern in ('/', 'm///', 's///', 'tr///'):
                    if match(s, i, pattern):
                        i = self.skip_regex(s, i, pattern)
                        break
            i += 1
            assert progress < i
        if trace:
            g.trace(self, s.rstrip())
        if gen_v2:
            return ScanState(
                self.context,
                curlies = self.curlies,
                tag = 'Perl',
            )
    #@+node:ekr.20161027094537.12: *3* perl_state.skip_regex
    def skip_regex(self, s, i, pattern):
        '''look ahead for a regex /'''
        trace = False and not g.unitTesting
        if trace: g.trace(repr(s), self.parens)
        assert self.match(s, i, pattern)
        i += len(pattern)
        while i < len(s) and s[i] in ' \t':
            i += 1
        if i < len(s) and s[i] == '/':
            i += 1
            while i < len(s):
                progress = i
                ch = s[i]
                if ch == '\\':
                    i += 2
                elif ch == '/':
                    i += 1
                    break
                else:
                    i += 1
                assert progress < i
        if trace: g.trace('returns', i, s[i] if i < len(s) else '')
        return i-1
    #@-others
#@+node:ekr.20161027094537.13: ** class PerlScanner
class PerlScanner(basescanner.BaseLineScanner):
    '''A scanner for the perl language.'''
    
    def __init__(self, importCommands, atAuto,language=None, alternate_language=None):
        '''The ctor for the PerlScanner class.'''
        c = importCommands.c
        clean = c.config.getBool('perl_importer_clean_lws', default=False)
        # Init the base class.
        basescanner.BaseLineScanner.__init__(self, importCommands,
            atAuto = atAuto,
            gen_clean = clean, # True: clean blank lines.
            gen_refs = False, # Don't generate section references.
            language = 'perl', # For @language.
            state = PerlStateScanner(c),
            strict = False, # True: leave leading whitespace alone.
        )
        
    #@+others
    #@+node:ekr.20161027183713.1: *3* perl.clean_headline
    def clean_headline(self, s):
        '''Return a cleaned up headline s.'''
        m = re.match(r'sub\s+(\w+)', s)
        return 'sub ' + m.group(1) if m else s
    #@+node:ekr.20161027194956.1: *3* perl.clean_nodes
    def clean_nodes(self, parent):
        '''Clean nodes as part of the post pass.'''
        # Move trailing comments into following def nodes.
        for p in parent.subtree():
            next = p.threadNext()
            lines = g.splitLines(p.b)
            if lines and next:
                while lines and lines[-1].strip().startswith('#'):
                    next.b = lines.pop() + next.b
                p.b = ''.join(lines)
    #@-others
#@-others
importer_dict = {
    'class': PerlScanner,
    'extensions': ['.pl',],
}
#@-leo