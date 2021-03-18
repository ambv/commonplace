module util {
    scalar type Slug extending str {
        constraint regexp(r'^[a-z0-9][.a-z0-9-]+$');
    };

    scalar type Tag extending str {
        constraint regexp(r'^[a-zA-Z0-9][a-zA-Z0-9./-]+$');
    };
};
