(include base.scm)

(unless (defined? __functional__)
        (define nest
                (lambda (f v n)
                        (if (= n 0)
                            v
                            (f (nest f v (- n 1))))))

        (define apply
                (lambda (f args)
                        (define N (len args))
                        (define build
                                (lambda (m)
                                        (if (= m N)
                                            nil
                                            (cons (list 'car
                                                        (nest (lambda (x) (list 'cdr' x))
                                                              'args
                                                              m))
                                                  (build (+ m 1))))))
                        (eval (cons f (build 0)))
                        ))

        (define fixed-point
                (lambda (f g)
                        (cons' g
                               (fixed-point f (f g)))))

        (define take-while
                (lambda (f l)
                        (if (f (car l))
                            (cons' (car l)
                                   (take-while f (cdr' l)))
                            nil)))

        (define expand
                (lambda (l)
                        (if (pair? l)
                            (cons (expand (car l))
                                  (expand (cdr' l)))
                            l)))

        (define any
                (lambda (l)
                        (cond ((nil? l) #f)
                              ((car l) (car l))
                              (else (any (cdr' l))))))


        (define zip
                (lambda (() . ls)
                        (if (any (map nil? ls))
                            nil
                            (cons' (map car ls)
                                   (apply zip (map cdr' ls))))))

        (define take-from
                (lambda (f l)
                        (if (f (car l))
                            l
                            (take-from f (cdr' l)))))

        (define take-until
                (lambda (f l)
                        (if (f (car l))
                            nil
                            (cons' (car l)
                                   (take-until f (cdr' l))))))

        (define take-when
                (lambda (f l)
                        (if (f (car l))
                            (car l)
                            (take-when f (cdr' l)))))

        (define count
                (lambda (n)
                        (cons' n (count (+ n 1)))))

        (define map
                (lambda (f l)
                        (if (nil? l)
                            nil
                            (cons' (f (car l))
                                   (map f (cdr' l))))))

        (define reduce
                (lambda (f s l)
                        (if (nil? l)
                            s
                            (f s
                               (reduce (car l) f (cdr' l))))))

        (define filter
                (lambda (f l)
                        (cond ((nil? l) nil)
                              ((f (car l)) (cons' (car l) (filter f (cdr' l))))
                              (else (filter f (cdr' l))))))

         (define join
                 (lambda (x y)
                         (if (nil? x)
                             y
                             (cons' (car x) (join (cdr' x) y)))))

         (define sort
                 (lambda (l cmp)
                         (if (nil? l)
                             nil
                             (let ((pivot (car l)))
                                  (join (sort (filter (lambda (e) (not (cmp e pivot)))
                                                      (cdr' l))
                                              cmp)
                                        (cons pivot
                                              (sort (filter (lambda (e) (cmp e pivot))
                                                            (cdr' l))
                                                    cmp)))))))

        (define take-n
                (lambda (n l)
                        (if (= n 0)
                            nil
                            (cons' (car l)
                                   (take-n (- n 1)
                                           (cdr' l))))))


        (define __functional__ nil))

