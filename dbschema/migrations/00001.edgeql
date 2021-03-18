CREATE MIGRATION m16vqivbi4kjz4zbmkuftcxkowdco5rvif2xt7saw3xaagr4phejwq
    ONTO initial
{
  CREATE MODULE util IF NOT EXISTS;
  CREATE MODULE commonplace IF NOT EXISTS;
  CREATE SCALAR TYPE util::Tag EXTENDING std::str {
      CREATE CONSTRAINT std::regexp('^[a-zA-Z0-9][a-zA-Z0-9./-]+$');
  };
  CREATE ABSTRACT TYPE commonplace::HasTags {
      CREATE MULTI PROPERTY tags -> util::Tag;
  };
  CREATE SCALAR TYPE util::Slug EXTENDING std::str {
      CREATE CONSTRAINT std::regexp('^[a-z0-9][.a-z0-9-]+$');
  };
  CREATE ABSTRACT TYPE commonplace::Named {
      CREATE REQUIRED PROPERTY name -> util::Slug {
          CREATE CONSTRAINT std::exclusive;
      };
      CREATE INDEX ON (__subject__.name);
  };
  CREATE ABSTRACT TYPE commonplace::Publishable {
      CREATE REQUIRED PROPERTY deleted -> std::bool;
      CREATE PROPERTY public_since -> std::datetime;
      CREATE PROPERTY public_until -> std::datetime;
  };
  CREATE ABSTRACT TYPE commonplace::Titled {
      CREATE OPTIONAL PROPERTY title -> std::str;
  };
  CREATE TYPE commonplace::Content EXTENDING commonplace::Named, commonplace::Titled, commonplace::Publishable, commonplace::HasTags;
  CREATE TYPE commonplace::Image EXTENDING commonplace::Content {
      CREATE REQUIRED PROPERTY image -> std::bytes;
  };
  CREATE TYPE commonplace::Note EXTENDING commonplace::Content {
      CREATE REQUIRED PROPERTY text -> std::str;
  };
  CREATE TYPE commonplace::User EXTENDING commonplace::Named;
};
