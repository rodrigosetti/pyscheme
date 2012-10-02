
; Fundamental macro, useful for the very definition of other objects
(define begin
        (macro ()
               ((begin ...) ...)))

(if (defined? __base__) nil
    (begin

     (define cadr
             (lambda (x)
                     (car (cdr x))))

     (define cadr'
             (lambda (x)
                     (car (cdr' x))))

     (define len
             (lambda (l)
                     (if (nil? l)
                         0
                         (+ 1 (len (cdr' l))))))

     (define not
             (lambda (e)
                     (if e #f #t)))

     (define !=
             (lambda (a b)
                     (if (= a b) #f #t)))

     (define cons'
             (macro ()
                    ((_ x y) (cons x (delay y)))))

     (define cdr'
             (macro ()
                    ((_ x) (if (thunk? (cdr x))
                               (eval (cdr x))
                               (cdr x)))))

     (define list
             (lambda (() . x) x))

     (define when
             (macro ()
                    ((when c ...) (if c (begin ...) nil))))

     (define unless
             (macro ()
                    ((unless c ...) (if c nil (begin ...)))))

     (define and
             (macro ()
                    ((_) #t)
                    ((_ e) e)
                    ((_ e1 e2 ...) (if e1 (and e2 ...) #f))))

     (define or
             (macro ()
                    ((_) #f)
                    ((_ e) e)
                    ((_ e1 e2 ...) (let ((t e1)) (if t t (or e2 ...))))))

     (define let
             (macro ()
                    ((let ((n v)) e ...) ((lambda () (define n v) e ...)))
                    ((let ((n v) ...1) e ...2) ((lambda () (define n v) (let (...1) e ...2))))))

     (define cond
             (macro (else)
                    ((cond (else e)) e)
                    ((cond (c e)) (if c e))
                    ((cond (c e) cl ...) (if c e (cond cl ...)))))

     (define __base__ nil)))

