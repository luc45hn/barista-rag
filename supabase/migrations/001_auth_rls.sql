-- Habilitar RLS globalmente para las tablas del proyecto
-- Se aplica después de crear las tablas en 002

alter table recipes enable row level security;

-- Policy: usuarios autenticados pueden ver recetas aprobadas
create policy "Authenticated users can view approved recipes"
  on recipes for select
  using (auth.role() = 'authenticated' and approved = true);

-- Policy: usuarios autenticados pueden insertar recetas
create policy "Authenticated users can insert recipes"
  on recipes for insert
  with check (auth.role() = 'authenticated');

-- Policy: usuarios autenticados pueden actualizar sus propias recetas
create policy "Authenticated users can update own recipes"
  on recipes for update
  using (auth.role() = 'authenticated' and created_by = auth.email());

-- Policy: usuarios autenticados pueden ver sus propias recetas pendientes
create policy "Authenticated users can view own pending recipes"
  on recipes for select
  using (auth.role() = 'authenticated' and created_by = auth.email());
