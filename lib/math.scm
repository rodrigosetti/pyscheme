(include base.scm)
(include functional.scm)

(unless (defined? __math__)

        (define average
                (lambda (() . x)
                        (/ (apply + x) (len x))))

        (define abs
                (lambda (x)
                        (if (< x 0)
                            (* x -1)
                            x)))

        (define count
                (lambda (x . xs)
                        (define start (if (nil? xs) 0 x))
                        (define step (if (nil? xs)
                                         x
                                         (car xs)))
                        (cons' start
                              (count (+ start step)
                                     step))))

        (define sqrt
                (lambda (x)
                        (take-when (lambda (v) (< (abs (- x (* v v))) 0.0001))
                                   (fixed-point (lambda (g) (average g (/ x g)))
                                                1.))))

;        Another way to define square root
;
;        (define sqrt
;                (lambda (x)
;                        (take-when (lambda (v) (< (abs (- x (* v v))) 0.0001))
;                                   (newton-method (lambda (y) (- (* y y) x)) 1))))

        (define numeric-derivative
                (lambda (f x)
                        (define h 0.00000001)
                        (/ (- (f (+ x h))
                              (f x))
                           h)))

        (define newton-method
               (lambda (f g)
                       (cons' g
                              (newton-method f
                                             (- g (/ (f g) (numeric-derivative f g)))))))

        (define __math__ nil))

