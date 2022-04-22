-- Exported from QuickDBD: https://www.quickdatabasediagrams.com/
-- Link to schema: https://app.quickdatabasediagrams.com/#/d/TfFxRs
-- NOTE! If you have used non-SQL datatypes in your design, you will have to change these here.

-- Modify this code to update the DB schema diagram.
-- To reset the sample schema, replace everything with
-- two dots ('..' - without quotes).

CREATE TABLE "User" (
    "UserId" int   NOT NULL,
    "RoleId" int   NOT NULL,
    "TelegramId" int   NOT NULL,
    "CreatedAt" date   NOT NULL,
    CONSTRAINT "pk_User" PRIMARY KEY (
        "UserId"
     )
);

CREATE TABLE "Role" (
    "RoleId"  SERIAL  NOT NULL,
    "Title" string   NOT NULL,
    CONSTRAINT "pk_Role" PRIMARY KEY (
        "RoleId"
     )
);

CREATE TABLE "Command" (
    "CommandId"  SERIAL  NOT NULL,
    "Title" string   NOT NULL,
    "Active" bool   NOT NULL,
    CONSTRAINT "pk_Command" PRIMARY KEY (
        "CommandId"
     )
);

CREATE TABLE "Definition" (
    "CreatedAt" date   NOT NULL,
    "UpdatedAt" date   NOT NULL,
    "DefinitionId"  SERIAL  NOT NULL,
    "DefinitionType" int   NOT NULL,
    "TermId" int   NOT NULL,
    "Content" string   NOT NULL,
    CONSTRAINT "pk_Definition" PRIMARY KEY (
        "DefinitionId"
     )
);

CREATE TABLE "DefinitionType" (
    "DefenitionTypeId"  SERIAL  NOT NULL,
    "Name" string   NOT NULL,
    CONSTRAINT "pk_DefinitionType" PRIMARY KEY (
        "DefenitionTypeId"
     )
);

CREATE TABLE "Term" (
    "TermId"  SERIAL  NOT NULL,
    "title" string   NOT NULL,
    "CreatedAt" date   NOT NULL,
    "UpdatedAt" date   NOT NULL,
    CONSTRAINT "pk_Term" PRIMARY KEY (
        "TermId"
     )
);

CREATE TABLE "Menu" (
    "MenuId" int   NOT NULL,
    "Image" BINARY   NOT NULL,
    "Active" bool   NOT NULL,
    "Title" str   NOT NULL,
    CONSTRAINT "pk_Menu" PRIMARY KEY (
        "MenuId"
     )
);

CREATE TABLE "Submenu" (
    "SubmenuId" int   NOT NULL,
    "MenuId" int   NOT NULL,
    "Active" bool   NOT NULL,
    "Image" BINARY   NOT NULL,
    CONSTRAINT "pk_Submenu" PRIMARY KEY (
        "SubmenuId"
     )
);

CREATE TABLE "Message" (
    "Id"  SERIAL  NOT NULL,
    "Title" str   NOT NULL,
    "Description" str   NOT NULL,
    CONSTRAINT "pk_Message" PRIMARY KEY (
        "Id"
     )
);

ALTER TABLE "User" ADD CONSTRAINT "fk_User_RoleId" FOREIGN KEY("RoleId")
REFERENCES "Role" ("RoleId");

ALTER TABLE "Definition" ADD CONSTRAINT "fk_Definition_DefinitionType" FOREIGN KEY("DefinitionType")
REFERENCES "DefinitionType" ("DefenitionTypeId");

ALTER TABLE "Definition" ADD CONSTRAINT "fk_Definition_TermId" FOREIGN KEY("TermId")
REFERENCES "Term" ("TermId");

ALTER TABLE "Submenu" ADD CONSTRAINT "fk_Submenu_MenuId" FOREIGN KEY("MenuId")
REFERENCES "Menu" ("MenuId");

