def compute(db: og.Database):
    a = db.inputs.target_pos
    b = db.inputs.current_pos

    a[1] -= 60
    a[2] += 90
    sub = [a[i] - b[i] for i in range(len(a))]
    add = [1, 1, 1, 1]

    for i in range(len(sub)):
        if sub[i] < -1:
            add[i] = -1
        elif sub[i] > 1:
            add[i] = 1
        else:
            add[i] = 0

    pos_cmd = [b[i] + add[i] for i in range(len(b))]

    db.outputs.pos_cmd = pos_cmd
    return True