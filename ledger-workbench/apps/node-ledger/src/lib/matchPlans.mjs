const fixedCatalog = {
  invoice: "^INV-[0-9]{6}$",
  merchant: "^[A-Z][A-Za-z .'-]{1,80}$",
  tenant: "^tenant-[a-z0-9-]{1,32}$",
  status: "^(settled|review|failed)$",
  amount: "^[0-9]{1,7}(\\.[0-9]{2})?$",
  route: "^/(reports|exports|billing)(/[a-z0-9-]+)?$",
  host: "^[a-z0-9.-]{1,80}$",
  memo: "^[\\w .,'-]{0,160}$",
  phone: "^\\+?[0-9 -]{7,20}$",
  date: "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
};

const modeCatalog = {
  compact: "i",
  exact: "",
  scan: "im",
  global: "g"
};

export function textPattern(value) {
  return String(value || "").slice(0, 300);
}

export function textFlags(value) {
  return String(value || "").replace(/[^gimsuy]/g, "").slice(0, 6);
}

export function catalogPattern(value) {
  return fixedCatalog[value] || fixedCatalog.memo;
}

export function catalogFlags(value) {
  return modeCatalog[value] ?? "";
}

export function literalPattern(value) {
  return String(value || "").replace(/[.*+?^${}()|[\]\\]/g, "\\$&").slice(0, 160);
}

export function compilePlanA(record) {
  const source = textPattern(record.pattern);
  return new RegExp(source, textFlags(record.flags));
}

export function compilePlanB(record) {
  const source = catalogPattern(record.kind);
  return new RegExp(source, catalogFlags(record.mode));
}

export function compilePlanC(record) {
  const source = textPattern(record.expression);
  return new RegExp(source, textFlags(record.options));
}

export function compilePlanD(record) {
  const source = literalPattern(record.expression);
  return new RegExp(source, catalogFlags(record.mode));
}

export function compilePlanE(record) {
  const source = textPattern(record.include);
  return new RegExp(source, textFlags(record.flags));
}

export function compilePlanF(record) {
  const source = catalogPattern(record.include);
  return new RegExp(source, "");
}

export function compilePlanG(record) {
  const source = textPattern(record.exclude);
  return new RegExp(source, textFlags(record.flags));
}

export function compilePlanH(record) {
  const source = literalPattern(record.exclude);
  return new RegExp(source, "");
}

export function compilePlanI(record) {
  const source = textPattern(record.keywords);
  return new RegExp(source, textFlags(record.flags));
}

export function compilePlanJ(record) {
  const source = catalogPattern(record.keywords);
  return new RegExp(source, catalogFlags(record.mode));
}

export function compilePlanK(record) {
  const source = textPattern(record.selector);
  return new RegExp(source, textFlags(record.flags));
}

export function compilePlanL(record) {
  const source = literalPattern(record.selector);
  return new RegExp(source, catalogFlags(record.mode));
}

export function compilePlanM(record) {
  const source = textPattern(record.window);
  return new RegExp(source, textFlags(record.flags));
}

export function compilePlanN(record) {
  const source = catalogPattern(record.window);
  return new RegExp(source, "");
}

export function compilePlanO(record) {
  const source = textPattern(record.routing);
  return new RegExp(source, textFlags(record.flags));
}

export function compilePlanP(record) {
  const source = literalPattern(record.routing);
  return new RegExp(source, "");
}

export function compilePlanQ(record) {
  const source = textPattern(record.bucket);
  return new RegExp(source, textFlags(record.flags));
}

export function compilePlanR(record) {
  const source = catalogPattern(record.bucket);
  return new RegExp(source, catalogFlags(record.mode));
}

export function compilePlanS(record) {
  const source = textPattern(record.marker);
  return new RegExp(source, textFlags(record.flags));
}

export function compilePlanT(record) {
  const source = literalPattern(record.marker);
  return new RegExp(source, catalogFlags(record.mode));
}

export function compilePlanU(record) {
  const source = textPattern(record.label);
  return new RegExp(source, textFlags(record.flags));
}

export function compilePlanV(record) {
  const source = catalogPattern(record.label);
  return new RegExp(source, "");
}

export function compilePlanW(record) {
  const source = textPattern(record.channel);
  return new RegExp(source, textFlags(record.flags));
}

export function compilePlanX(record) {
  const source = literalPattern(record.channel);
  return new RegExp(source, "");
}

export function compilePlanY(record) {
  const source = textPattern(record.group);
  return new RegExp(source, textFlags(record.flags));
}

export function compilePlanZ(record) {
  const source = catalogPattern(record.group);
  return new RegExp(source, catalogFlags(record.mode));
}

export function compilePlanAA(record) {
  const source = textPattern(record.filter);
  return new RegExp(source, textFlags(record.flags));
}

export function compilePlanAB(record) {
  const source = literalPattern(record.filter);
  return new RegExp(source, catalogFlags(record.mode));
}

export function compilePlanAC(record) {
  const source = textPattern(record.rule);
  return new RegExp(source, textFlags(record.flags));
}

export function compilePlanAD(record) {
  const source = catalogPattern(record.rule);
  return new RegExp(source, "");
}

export function compilePlanAE(record) {
  const source = textPattern(record.term);
  return new RegExp(source, textFlags(record.flags));
}

export function compilePlanAF(record) {
  const source = literalPattern(record.term);
  return new RegExp(source, "");
}

export function compilePlanAG(record) {
  const source = textPattern(record.reference);
  return new RegExp(source, textFlags(record.flags));
}

export function compilePlanAH(record) {
  const source = catalogPattern(record.reference);
  return new RegExp(source, catalogFlags(record.mode));
}

export function compilePlanAI(record) {
  const source = textPattern(record.entry);
  return new RegExp(source, textFlags(record.flags));
}

export function compilePlanAJ(record) {
  const source = literalPattern(record.entry);
  return new RegExp(source, catalogFlags(record.mode));
}

export function compilePlanAK(record) {
  const source = textPattern(record.note);
  return new RegExp(source, textFlags(record.flags));
}

export function compilePlanAL(record) {
  const source = catalogPattern(record.note);
  return new RegExp(source, "");
}

export function compilePlanAM(record) {
  const source = textPattern(record.tag);
  return new RegExp(source, textFlags(record.flags));
}

export function compilePlanAN(record) {
  const source = literalPattern(record.tag);
  return new RegExp(source, "");
}
