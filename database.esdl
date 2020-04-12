module commonplace {
    ### high-level object types

    type Note extending Versioned {
        required property text -> str;
    }

    type Image extending Versioned {
        required property image -> bytes;
    }

    type Content extending Titled, Named, HasTags, Publishable {
        # `latest` needs to be updated when a new Version is
        # inserted with `parent` set to the current `latest`.
        required link latest -> Versioned {
            constraint exclusive;
        };
    }

    type User extending Named;

    ### abstract types

    abstract type Versioned {
        required property sha1 -> SHA1;
        required property ts -> datetime;
        required link editor -> User;
        link parent -> Versioned {
            # Conflicts are to be fixed on the client side.
            constraint exclusive;
        };
    }

    abstract type Titled {
        # Describes an optional non-unique human-readable title.
        property title -> str;
    }

    abstract type Named {
        # Described a unique URL-safe slug-style name.
        required property name -> Slug {
            constraint exclusive;
        };
        index on (__subject__.name);
    }

    abstract type HasTags {
        multi property tags -> Tag;
    }

    abstract type Publishable {
        property public_since -> datetime;
        property public_until -> datetime;
        property deleted -> bool;
    }

    ### custom scalars

    scalar type Slug extending str {
        constraint regexp(r'^[a-z0-9][.a-z0-9-]+$');
    }

    scalar type Tag extending str {
        constraint regexp(r'^[a-zA-Z0-9][a-zA-Z0-9./-]+$')
    }

    scalar type SHA1 extending bytes {
        constraint min_bytes_len(20);
        constraint max_bytes_len(20);
    }

    ### custom constraints
    abstract constraint max_bytes_len(max: int64) on (len(<std::bytes>__subject__)) extending max_value {
        errmessage := '{__subject__} must be no longer than {max} bytes.';
    }

    abstract constraint min_bytes_len(min: int64) on (len(<std::bytes>__subject__)) extending min_value {
        errmessage := '{__subject__} must be no shorter than {min} bytes.';
    }
}
