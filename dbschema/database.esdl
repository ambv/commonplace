module commonplace {
    type User extending
        Named;

    type Content extending
        Named,
        Titled,
        Publishable,
        HasTags;

    type Note extending Content {
        required property text -> str;
    };

    type Image extending Content {
        required property image -> bytes;
    };

    abstract type Named {
        required property name -> util::Slug {
            constraint exclusive;
        };
        index on (__subject__.name);
    };

    abstract type Titled {
        optional property title -> str;
    };

    abstract type Publishable {
        property public_since -> datetime;
        property public_until -> datetime;
        required property deleted -> bool;
    };

    abstract type HasTags {
        multi property tags -> util::Tag;
    };
};
