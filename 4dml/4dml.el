
;;    4DML Transformation Utility
;;
;;    (C) 2006 Silas S. Brown (University of Cambridge Computer Laboratory,
;;        Cambridge, UK, http://www.cus.cam.ac.uk/~ssb22 )
;;
;;     This program is free software; you can redistribute it and/or modify
;;     it under the terms of the GNU General Public License as published by
;;     the Free Software Foundation; either version 2 of the License, or
;;     (at your option) any later version.
;;
;;     This program is distributed in the hope that it will be useful,
;;     but WITHOUT ANY WARRANTY; without even the implied warranty of
;;     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
;;     GNU General Public License for more details.
;;
;;     You should have received a copy of the GNU General Public License
;;     along with this program; see the file COPYING.  If not, write to
;;     the Free Software Foundation, Inc., 59 Temple Place - Suite 330,
;;     Boston, MA 02111-1307, USA.


;; A major mode for editing 4DML MML files
;; Provides simple syntax highlighting

;; Note: This should highlight reasonably correctly when
;; doing font-lock-fontify-buffer, but might not be so good
;; when actually editing, especially when editing !block
;; constructs, since font-lock only considers one line at a
;; time.  c.f. HTML mode problems in comments etc.

(defun 4dml-para-end ()
  (let ((retval nil))
    (save-excursion
      (setq 4dml-font-oldpos (point))
      (forward-paragraph)
      (setq retval (point)))
    retval))
(defun 4dml-restore-posn ()
  (goto-char 4dml-font-oldpos))
(defconst 4dml-font-lock-keywords
  (list
   ;; Anything between !block and !endblock should first be
   ;; set to the default face.  !block's own markup will
   ;; override this (using 't' after the face name), but
   ;; other markup (begin, end etc) won't.
   '("!block\\([^!]\\|![^e]\\|!e[^n]\\|!en[^d]\\|!end[^b]\\|!endb[^l]\\|!endbl[^o]\\|!endblo[^c]\\|!endbloc[^k]\\)*" (0 'default))
   '("!block"
     (0 font-lock-keyword-face t)
     ;; begin !block anchor matches
     ;; First, have default for all words in block header
     ;; Subsequent matches override this (by using 't' after the face)
     ("[ \t\n\f]\\([^ \t\n\f]+\\)" (4dml-para-end) (4dml-restore-posn) (1 font-lock-reference-face t))
     ("[ \t\n\f]\\(have\\)[ \t\n\f]" (4dml-para-end) (4dml-restore-posn) (1 font-lock-keyword-face t))
     ("[ \t\n\f]\\(as\\)[ \t\n\f]" (4dml-para-end) (4dml-restore-posn) (1 font-lock-keyword-face t))
     ("[ \t\n\f]\\(also\\)[ \t\n\f]" (4dml-para-end) (4dml-restore-posn) (1 font-lock-keyword-face t))
     ("[ \t\n\f]\\(special:\\)[ \t\n\f]" (4dml-para-end) (4dml-restore-posn) (1 font-lock-keyword-face t))
     ;; did have these within "special:" (and "nil nil" instead of "(4dml-para-end) (4dml-restore-posn)") but doesn't seem to work
     ("[ \t\n\f]\\(maximum\\)[ \t\n\f]" (4dml-para-end) (4dml-restore-posn) (1 font-lock-keyword-face t))
     ("[ \t\n\f]\\(per\\)[ \t\n\f]" (4dml-para-end) (4dml-restore-posn) (1 font-lock-keyword-face t))
     ("[ \t\n\f]\\(switches\\)[ \t\n\f]" (4dml-para-end) (4dml-restore-posn) (1 font-lock-keyword-face t))
     ;; end of "special:" anchor matches
     ) ;; end of !block anchor matches
   '("!endblock" (0 font-lock-keyword-face t))
   '("\\([^ \t\n\f]+\\)\\(:\\)[ \t\n\f]\\([^\n]*\\)" ;; elem: val
     (1 font-lock-function-name-face)
     (2 font-lock-keyword-face)
     (3 font-lock-variable-name-face))
   '("\\(begin\\|advance\\|end\\)[ \t\n\f]+[^ \t\n\f]+"
     (0 font-lock-type-face))
   ) "Expressions to highlight in 4DML MML mode" )

(defun 4dml-mml-mode ()
  "Major mode for editing 4DML MML files"
  (interactive)
  (kill-all-local-variables)
  (setq major-mode '4dml-mml-mode)
  (setq mode-name "4DML")
  (make-local-variable 'font-lock-defaults)
  (setq font-lock-defaults
        '(4dml-font-lock-keywords
          t ;; t=keywords only (no strings + comments)
          t ;; t=ignore case
          nil ;; syntax-alist
          ;; function to move backwards outside syntactic block (backward-paragraph, beginning-of-line etc)
          (font-lock-mark-block-function . mark-whole-buffer)))
  (font-lock-mode)
)
(provide '4dml-mml-mode)
