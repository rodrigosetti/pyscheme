(include base.scm)
(include functional.scm)

(unless (defined? __math__)

        ; Mathematical functions
        (define average
                (lambda (() . x)
                        (/ (apply + x) (len x))))

        (define abs
                (lambda (x)
                        (if (< x 0)
                            (* x -1)
                            x)))

        (define sqrt
                (lambda (x)
                        (take-when (lambda (v) (< (abs (- x (* v v))) 0.0001))
                                   (fixed-point (lambda (g) (average g (/ x g)))
                                                1.))))

        (define __math__ nil))

