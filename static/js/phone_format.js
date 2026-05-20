function formatUzPhoneInput(input) {
  const raw = input.value.replace(/\D/g, '');
  let digits = raw;

  if (digits.startsWith('998')) digits = digits.slice(3);
  digits = digits.slice(0, 9);

  let out = '+998';
  if (digits.length > 0) out += ` ${digits.slice(0, 2)}`;
  if (digits.length > 2) out += `-${digits.slice(2, 5)}`;
  if (digits.length > 5) out += `-${digits.slice(5, 7)}`;
  if (digits.length > 7) out += `-${digits.slice(7, 9)}`;

  input.value = out;
}

document.querySelectorAll('#id_phone_primary, #id_phone_secondary, #id_username, .phone-input').forEach((input) => {
  input.addEventListener('input', () => formatUzPhoneInput(input));
  if (input.value) formatUzPhoneInput(input);
});
