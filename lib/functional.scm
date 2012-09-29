(include base.scm)

(unless (defined? __functional__)
        ; Functional tools
        (define apply
                (lambda (f l)
                        (eval (cons f l))))

        (define fixed-point
                (lambda (f g)
                        (cons' g
                               (fixed-point f (f g)))))

        (define take-when
                (lambda (f l)
                        (if (f (car l))
                            (car l)
                            (take-when f (cdr' l)))))

        (define __functional__ nil))

